"""YApi MCP Server - Main server module with fastmcp."""

import json
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import cache
from typing import Annotated, Any

import httpx
from fastmcp import FastMCP

from yapi_mcp.config import ServerConfig
from yapi_mcp.yapi.client import YApiClient
from yapi_mcp.yapi.errors import (
    ERROR_TYPE_NETWORK_ERROR,
    format_tool_error,
    map_http_error_to_mcp,
)


class MCPToolError(RuntimeError):
    """Base exception for MCP tool failures."""


class MCPHTTPError(MCPToolError):
    """Exception raised when YApi returns an HTTP error."""


class MCPValidationError(MCPToolError):
    """Exception raised when tool input validation fails."""


class InvalidInterfacePathError(ValueError):
    """Raised when an interface path does not start with a slash."""

    def __init__(self) -> None:
        super().__init__("接口路径必须以 / 开头")


def _http_error_to_tool_error(
    error: httpx.HTTPStatusError,
    operation: str,
    params: dict[str, Any],
) -> MCPHTTPError:
    mcp_error = map_http_error_to_mcp(error)
    yapi_error_data = mcp_error.data.get("yapi_error") if mcp_error.data else None
    error_json = format_tool_error(
        error_type=mcp_error.error_type,
        message=mcp_error.message,
        operation=operation,
        params=params,
        error_code=mcp_error.code,
        retryable=mcp_error.retryable,
        yapi_error=yapi_error_data if isinstance(yapi_error_data, dict) else None,
    )
    return MCPHTTPError(error_json)


def _network_error_to_tool_error(
    error: Exception,
    operation: str,
    params: dict[str, Any],
) -> MCPToolError:
    error_json = format_tool_error(
        error_type=ERROR_TYPE_NETWORK_ERROR,
        message=f"网络错误: {error!s}",
        operation=operation,
        params=params,
        error_code=-32000,
        retryable=True,
    )
    return MCPToolError(error_json)


def _wrap_validation_error(error: ValueError) -> MCPValidationError:
    message = f"参数验证失败: {error!s}"
    return MCPValidationError(message)


def _wrap_tool_error(prefix: str, error: Exception) -> MCPToolError:
    message = f"{prefix}: {error!s}"
    return MCPToolError(message)


def _ensure_path_starts_with_slash(path: str) -> None:
    if not path.startswith("/"):
        raise InvalidInterfacePathError


SEARCH_INTERFACES_ERROR = "搜索接口失败"
GET_INTERFACE_ERROR = "获取接口失败"
CREATE_INTERFACE_ERROR = "创建接口失败"
UPDATE_INTERFACE_ERROR = "更新接口失败"


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
    config = get_config()
    try:
        async with YApiClient(str(config.yapi_server_url), config.cookies) as client:
            user_info = await client.check_login_status()
            username = user_info.get("username", "unknown")
            print(f"[yapi-mcp] Credentials validated: logged in as {username}", file=sys.stderr)
    except httpx.HTTPStatusError:
        print("[yapi-mcp] ERROR: Credential validation failed. Cookie may be expired.", file=sys.stderr)
        print("[yapi-mcp] Check YAPI_TOKEN and YAPI_UID environment variables.", file=sys.stderr)
        sys.exit(1)
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        print(f"[yapi-mcp] ERROR: Cannot connect to YApi at {config.yapi_server_url}: {exc}", file=sys.stderr)
        print("[yapi-mcp] Check YAPI_SERVER_URL environment variable.", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"[yapi-mcp] ERROR: Unexpected error during startup validation: {exc}", file=sys.stderr)
        sys.exit(1)
    yield {}


# Initialize MCP server
mcp = FastMCP(
    "YApi MCP Server",
    version="0.1.0",
    lifespan=app_lifespan,
)


@cache
def get_config() -> ServerConfig:
    """Get or create ServerConfig instance (cached)."""
    return ServerConfig()


# Tool implementations will be added in subsequent tasks (T019-T022)


@mcp.tool()
async def yapi_search_interfaces(
    project_id: Annotated[int, "YApi 项目 ID"],
    keyword: Annotated[str, "搜索关键词(匹配接口标题/路径/描述)"],
) -> str:
    """在指定 YApi 项目中搜索接口,支持按标题、路径、描述模糊匹配."""
    config = get_config()
    operation = "yapi_search_interfaces"
    params = {"project_id": project_id, "keyword": keyword}

    try:
        async with YApiClient(str(config.yapi_server_url), config.cookies) as client:
            results = await client.search_interfaces(project_id, keyword)
            return json.dumps(
                [result.model_dump(by_alias=True) for result in results],
                ensure_ascii=False,
                indent=2,
            )
    except MCPToolError:
        raise
    except httpx.HTTPStatusError as exc:
        raise _http_error_to_tool_error(exc, operation, params) from exc
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        raise _network_error_to_tool_error(exc, operation, params) from exc
    except Exception as exc:
        prefix = SEARCH_INTERFACES_ERROR
        raise _wrap_tool_error(prefix, exc) from exc


@mcp.tool()
async def yapi_get_interface(
    interface_id: Annotated[int, "接口 ID"],
) -> str:
    """获取 YApi 接口的完整定义(包括请求参数、响应结构、描述等)."""
    config = get_config()
    operation = "yapi_get_interface"
    params = {"interface_id": interface_id}

    try:
        async with YApiClient(str(config.yapi_server_url), config.cookies) as client:
            interface = await client.get_interface(interface_id)
            return json.dumps(
                interface.model_dump(by_alias=True),
                ensure_ascii=False,
                indent=2,
            )
    except MCPToolError:
        raise
    except httpx.HTTPStatusError as exc:
        raise _http_error_to_tool_error(exc, operation, params) from exc
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        raise _network_error_to_tool_error(exc, operation, params) from exc
    except Exception as exc:
        prefix = GET_INTERFACE_ERROR
        raise _wrap_tool_error(prefix, exc) from exc


@mcp.tool()
async def yapi_create_interface(
    project_id: Annotated[int, "项目 ID"],
    catid: Annotated[int, "分类 ID"],
    title: Annotated[str, "接口标题"],
    path: Annotated[str, "接口路径(以/开头)"],
    method: Annotated[str, "HTTP方法(GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS)"],
    req_body: Annotated[str, "请求体定义(JSON Schema字符串)"] = "",
    req_body_type: Annotated[str | None, "请求体类型(form/json/raw/file)"] = None,
    req_body_is_json_schema: Annotated[bool | None, "请求体是否为JSON Schema"] = None,
    req_body_form: Annotated[
        str, '表单字段(JSON数组:[{"name":"x","type":"text","required":"1","desc":"说明"}])'
    ] = "",
    res_body: Annotated[str, "响应体定义(JSON Schema字符串)"] = "",
    res_body_type: Annotated[str | None, "响应体类型(json/raw)"] = None,
    res_body_is_json_schema: Annotated[bool | None, "响应体是否为JSON Schema"] = None,
    req_query: Annotated[
        str, 'Query参数(JSON数组:[{"name":"page","required":"1","desc":"页码"}])'
    ] = "",
    req_headers: Annotated[
        str, '请求头(JSON数组:[{"name":"Authorization","value":"Bearer token","required":"1"}])'
    ] = "",
    req_params: Annotated[
        str, '路径参数(JSON数组:[{"name":"id","example":"123","desc":"用户ID"}])'
    ] = "",
    markdown: Annotated[str, "接口描述(Markdown格式,自动转HTML)"] = "",
    status: Annotated[str | None, "接口状态(undone/done)"] = None,
    tag: Annotated[str, '标签(JSON数组:["标签1","标签2"])'] = "",
    api_opened: Annotated[bool | None, "是否公开API"] = None,
) -> str:
    """在 YApi 项目中创建新接口。"""
    config = get_config()
    operation = "yapi_create_interface"
    params = {
        "project_id": project_id,
        "catid": catid,
        "title": title,
        "path": path,
        "method": method,
    }

    try:
        _ensure_path_starts_with_slash(path)

        async with YApiClient(str(config.yapi_server_url), config.cookies) as client:
            result = await client.create_interface(
                project_id=project_id,
                catid=catid,
                title=title,
                path=path,
                method=method,
                req_body=req_body,
                req_body_type=req_body_type,
                req_body_is_json_schema=req_body_is_json_schema,
                req_body_form=req_body_form,
                res_body=res_body,
                res_body_type=res_body_type,
                res_body_is_json_schema=res_body_is_json_schema,
                req_query=req_query,
                req_headers=req_headers,
                req_params=req_params,
                markdown=markdown,
                status=status,
                tag=tag,
                api_opened=api_opened,
            )
            return json.dumps(
                {
                    "action": result["action"],
                    "interface_id": result["interface_id"],
                    "message": "接口创建成功",
                },
                ensure_ascii=False,
            )
    except MCPToolError:
        raise
    except httpx.HTTPStatusError as exc:
        raise _http_error_to_tool_error(exc, operation, params) from exc
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        raise _network_error_to_tool_error(exc, operation, params) from exc
    except ValueError as exc:
        raise _wrap_validation_error(exc) from exc
    except Exception as exc:
        prefix = CREATE_INTERFACE_ERROR
        raise _wrap_tool_error(prefix, exc) from exc


@mcp.tool()
async def yapi_update_interface(
    interface_id: Annotated[int, "接口 ID"],
    catid: Annotated[int | None, "分类 ID(不传则保持原值)"] = None,
    title: Annotated[str | None, "接口标题"] = None,
    path: Annotated[str | None, "接口路径(以/开头)"] = None,
    method: Annotated[str | None, "HTTP方法(GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS)"] = None,
    req_body: Annotated[str | None, "请求体定义(JSON Schema字符串)"] = None,
    req_body_type: Annotated[str | None, "请求体类型(form/json/raw/file)"] = None,
    req_body_is_json_schema: Annotated[bool | None, "请求体是否为JSON Schema"] = None,
    req_body_form: Annotated[
        str | None,
        '表单字段(JSON数组:[{"name":"x","type":"text","required":"1","desc":"说明"}])',
    ] = None,
    res_body: Annotated[str | None, "响应体定义(JSON Schema字符串)"] = None,
    res_body_type: Annotated[str | None, "响应体类型(json/raw)"] = None,
    res_body_is_json_schema: Annotated[bool | None, "响应体是否为JSON Schema"] = None,
    req_query: Annotated[
        str | None, 'Query参数(JSON数组:[{"name":"page","required":"1","desc":"页码"}])'
    ] = None,
    req_headers: Annotated[
        str | None,
        '请求头(JSON数组:[{"name":"Authorization","value":"Bearer token","required":"1"}])',
    ] = None,
    req_params: Annotated[
        str | None, '路径参数(JSON数组:[{"name":"id","example":"123","desc":"用户ID"}])'
    ] = None,
    markdown: Annotated[str | None, "接口描述(Markdown格式,自动转HTML)"] = None,
    status: Annotated[str | None, "接口状态(undone/done)"] = None,
    tag: Annotated[str | None, '标签(JSON数组:["标签1","标签2"])'] = None,
    api_opened: Annotated[bool | None, "是否公开API"] = None,
    switch_notice: Annotated[bool | None, "是否通知团队成员"] = None,
    message: Annotated[str | None, "变更说明"] = None,
) -> str:
    """增量更新 YApi 接口定义。自动获取现有数据并合并,仅更新传入的字段。"""
    config = get_config()
    operation = "yapi_update_interface"
    params = {"interface_id": interface_id}

    try:
        if path is not None:
            _ensure_path_starts_with_slash(path)

        async with YApiClient(str(config.yapi_server_url), config.cookies) as client:
            result = await client.update_interface(
                interface_id=interface_id,
                catid=catid,
                title=title,
                path=path,
                method=method,
                req_body=req_body,
                req_body_type=req_body_type,
                req_body_is_json_schema=req_body_is_json_schema,
                req_body_form=req_body_form,
                res_body=res_body,
                res_body_type=res_body_type,
                res_body_is_json_schema=res_body_is_json_schema,
                req_query=req_query,
                req_headers=req_headers,
                req_params=req_params,
                markdown=markdown,
                status=status,
                tag=tag,
                api_opened=api_opened,
                switch_notice=switch_notice,
                message=message,
            )
            return json.dumps(
                {
                    "action": result["action"],
                    "interface_id": result["interface_id"],
                    "message": "接口更新成功",
                },
                ensure_ascii=False,
            )
    except MCPToolError:
        raise
    except httpx.HTTPStatusError as exc:
        raise _http_error_to_tool_error(exc, operation, params) from exc
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        raise _network_error_to_tool_error(exc, operation, params) from exc
    except ValueError as exc:
        raise _wrap_validation_error(exc) from exc
    except Exception as exc:
        prefix = UPDATE_INTERFACE_ERROR
        raise _wrap_tool_error(prefix, exc) from exc


def main() -> None:
    """Entry point for uvx yapi-mcp command."""
    mcp.run()


if __name__ == "__main__":
    main()
