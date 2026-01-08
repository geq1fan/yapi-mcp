"""YApi MCP Server - Main server module with fastmcp."""

import json
from functools import cache
from typing import Annotated, Any

import httpx
from fastmcp import FastMCP

from yapi_mcp.config import ServerConfig
from yapi_mcp.yapi.client import YApiClient
from yapi_mcp.yapi.errors import (
    ERROR_TYPE_NETWORK_ERROR,
    ERROR_TYPE_VALIDATION_FAILED,
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
SAVE_INTERFACE_ERROR = "保存接口失败"


# Initialize MCP server
mcp = FastMCP(
    "YApi MCP Server",
    version="0.1.0",
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
async def yapi_save_interface(
    catid: Annotated[int, "分类 ID (必需)"],
    project_id: Annotated[int, "项目 ID (创建时必需)"] = 0,
    interface_id: Annotated[int, "接口 ID (有值=更新,无值=创建)"] = 0,
    title: Annotated[str, "接口标题 (创建时必需)"] = "",
    path: Annotated[str, "接口路径 (创建时必需,以/开头)"] = "",
    method: Annotated[str, "HTTP方法 (创建时必需)"] = "",
    req_body: Annotated[str, "请求参数(JSON字符串)"] = "",
    res_body: Annotated[str, "响应结构(JSON字符串)"] = "",
    markdown: Annotated[str, "接口描述(Markdown格式)"] = "",
    req_body_type: Annotated[str | None, "请求体类型(form/json/raw/file)"] = None,
    req_body_is_json_schema: Annotated[bool | None, "请求体是否为JSON Schema"] = None,
    res_body_type: Annotated[str | None, "响应体类型(json/raw)"] = None,
    res_body_is_json_schema: Annotated[bool | None, "响应体是否为JSON Schema"] = None,
) -> str:
    """保存 YApi 接口定义。interface_id 有值则更新,无值则创建新接口。"""
    config = get_config()
    operation = "yapi_save_interface"
    params = {
        "catid": catid,
        "project_id": project_id,
        "interface_id": interface_id,
        "title": title,
        "path": path,
        "method": method,
    }

    try:
        if path and not path.startswith("/"):
            raise InvalidInterfacePathError

        async with YApiClient(str(config.yapi_server_url), config.cookies) as client:
            result = await client.save_interface(
                catid=catid,
                project_id=project_id if project_id else None,
                interface_id=interface_id if interface_id else None,
                title=title if title else None,
                path=path if path else None,
                method=method if method else None,
                req_body=req_body,
                res_body=res_body,
                markdown=markdown,
                req_body_type=req_body_type,
                req_body_is_json_schema=req_body_is_json_schema,
                res_body_type=res_body_type if res_body_type else None,
                res_body_is_json_schema=res_body_is_json_schema,
            )
            action = result["action"]
            iface_id = result["interface_id"]
            message = "接口创建成功" if action == "created" else "接口更新成功"
            return json.dumps(
                {"action": action, "interface_id": iface_id, "message": message},
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
        prefix = SAVE_INTERFACE_ERROR
        raise _wrap_tool_error(prefix, exc) from exc


def main() -> None:
    """Entry point for uvx yapi-mcp command."""
    mcp.run()


if __name__ == "__main__":
    main()
