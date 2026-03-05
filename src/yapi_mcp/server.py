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
    ERROR_TYPE_VALIDATION_FAILED,
    MCP_CODE_INVALID_PARAMS,
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


def _wrap_validation_error(
    error: ValueError,
    operation: str,
    params: dict[str, Any],
) -> MCPValidationError:
    error_json = format_tool_error(
        error_type=ERROR_TYPE_VALIDATION_FAILED,
        message=f"参数验证失败: {error!s}",
        operation=operation,
        params=params,
        error_code=MCP_CODE_INVALID_PARAMS,
        retryable=False,
    )
    return MCPValidationError(error_json)


def _wrap_tool_error(prefix: str, error: Exception) -> MCPToolError:
    message = f"{prefix}: {error!s}"
    return MCPToolError(message)


def _ensure_path_starts_with_slash(path: str) -> None:
    if not path.startswith("/"):
        raise InvalidInterfacePathError


_VALID_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
_VALID_REQ_BODY_TYPES = {"form", "json", "raw", "file"}
_VALID_RES_BODY_TYPES = {"json", "raw"}
_VALID_STATUSES = {"undone", "done"}

_JSON_ARRAY_FIELD_EXAMPLES = {
    "req_body_form": '[{"name":"field1","type":"text","required":1,"desc":"字段说明"}]',
    "req_query": '[{"name":"page","required":0,"desc":"页码","example":"1"}]',
    "req_headers": '[{"name":"Authorization","value":"Bearer token","required":1}]',
    "req_params": '[{"name":"id","example":"123","desc":"用户ID"}]',
    "tag": '["标签1","标签2"]',
}


def _validate_interface_request(
    *,
    method: str | None = None,
    req_body_type: str | None = None,
    req_body: str | None = None,
    req_body_form: str | None = None,
    res_body_type: str | None = None,
    status: str | None = None,
    req_query: str | None = None,
    req_headers: str | None = None,
    req_params: str | None = None,
    tag: str | None = None,
) -> None:
    """Validate cross-field constraints for interface create/update requests.

    Treats both None and "" as "not provided" to unify create (default "")
    and update (default None) tool signatures.
    """

    def _provided(v: str | None) -> bool:
        return bool(v)

    # 1. Enum value validation
    if method is not None and method not in _VALID_METHODS:
        raise ValueError(
            f'method "{method}" 无效。'
            f"支持的 HTTP 方法为：{'、'.join(sorted(_VALID_METHODS))}。"
        )

    if req_body_type is not None and req_body_type not in _VALID_REQ_BODY_TYPES:
        raise ValueError(
            f'req_body_type "{req_body_type}" 无效。'
            "支持的值为：form（表单）、json（JSON 格式）、raw（原始文本）、file（文件上传）。"
        )

    if res_body_type is not None and res_body_type not in _VALID_RES_BODY_TYPES:
        raise ValueError(
            f'res_body_type "{res_body_type}" 无效。支持的值为：json、raw。'
        )

    if status is not None and status not in _VALID_STATUSES:
        raise ValueError(
            f'status "{status}" 无效。支持的值为：undone（未完成）、done（已完成）。'
        )

    has_req_body = _provided(req_body)
    has_req_body_form = _provided(req_body_form)

    # 2. Mutual exclusion: req_body and req_body_form cannot both be provided
    if has_req_body and has_req_body_form:
        raise ValueError(
            "req_body 和 req_body_form 不能同时提供："
            "req_body 用于 json/raw 类型的请求体（字符串格式），"
            "req_body_form 用于 form 类型的请求体（JSON 数组格式）。"
            "请根据 req_body_type 选择其中一个。"
        )

    # 3. Body type correlation
    if req_body_type == "form" and has_req_body:
        raise ValueError(
            'req_body_type 为 "form" 时，请求体字段应通过 req_body_form 以 JSON 数组格式定义'
            '（如 [{"name":"field1","type":"text","required":1,"desc":""}]），'
            "而非 req_body。req_body 仅用于 json/raw 类型。"
            "请清空 req_body，将字段定义移至 req_body_form。"
        )

    if req_body_type in ("json", "raw") and has_req_body_form:
        raise ValueError(
            f'req_body_type 为 "{req_body_type}" 时，请求体应通过 req_body 提供（字符串格式），'
            "而非 req_body_form。req_body_form 仅用于 form 类型。"
            "请清空 req_body_form，将内容移至 req_body。"
        )

    if req_body_type == "file" and (has_req_body or has_req_body_form):
        raise ValueError(
            'req_body_type 为 "file" 时，不需要提供 req_body 或 req_body_form，'
            "文件上传接口的字段通过 YApi 界面配置。请清空这两个字段。"
        )

    # 4. JSON array format pre-validation
    json_array_fields: dict[str, str | None] = {
        "req_body_form": req_body_form,
        "req_query": req_query,
        "req_headers": req_headers,
        "req_params": req_params,
        "tag": tag,
    }
    for field_name, field_value in json_array_fields.items():
        if not _provided(field_value):
            continue
        example = _JSON_ARRAY_FIELD_EXAMPLES[field_name]
        try:
            parsed = json.loads(field_value)  # type: ignore[arg-type]
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"{field_name} 必须是合法的 JSON 数组格式（如 {example}），"
                f"当前值无法解析为 JSON：{exc.msg}。"
            ) from exc
        if not isinstance(parsed, list):
            raise ValueError(
                f"{field_name} 必须是 JSON 数组格式（以 [ 开头，以 ] 结尾），"
                f"如：{example}。当前值解析后不是数组类型。"
            )


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
        _validate_interface_request(
            method=method,
            req_body_type=req_body_type,
            req_body=req_body,
            req_body_form=req_body_form,
            res_body_type=res_body_type,
            status=status,
            req_query=req_query,
            req_headers=req_headers,
            req_params=req_params,
            tag=tag,
        )

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
        raise _wrap_validation_error(exc, operation, params) from exc
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
        _validate_interface_request(
            method=method,
            req_body_type=req_body_type,
            req_body=req_body,
            req_body_form=req_body_form,
            res_body_type=res_body_type,
            status=status,
            req_query=req_query,
            req_headers=req_headers,
            req_params=req_params,
            tag=tag,
        )

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
        raise _wrap_validation_error(exc, operation, params) from exc
    except Exception as exc:
        prefix = UPDATE_INTERFACE_ERROR
        raise _wrap_tool_error(prefix, exc) from exc


def main() -> None:
    """Entry point for uvx yapi-mcp command."""
    mcp.run()


if __name__ == "__main__":
    main()
