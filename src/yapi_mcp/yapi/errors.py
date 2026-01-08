"""Error mapping from YApi/HTTP errors to MCP errors."""

import json
from collections.abc import Mapping
from typing import Any, Literal, NotRequired, TypedDict

import httpx

ErrorData = dict[str, object]

ERROR_TYPE_AUTH_FAILED = "AUTH_FAILED"
ERROR_TYPE_RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
ERROR_TYPE_PERMISSION_DENIED = "PERMISSION_DENIED"
ERROR_TYPE_INVALID_PARAMS = "INVALID_PARAMS"
ERROR_TYPE_VALIDATION_FAILED = "VALIDATION_FAILED"
ERROR_TYPE_SERVER_ERROR = "SERVER_ERROR"
ERROR_TYPE_NETWORK_ERROR = "NETWORK_ERROR"
ERROR_TYPE_CONFIG_ERROR = "CONFIG_ERROR"


class ToolErrorDetails(TypedDict, total=False):
    operation: str
    params: dict[str, Any]
    error_code: int
    yapi_error: NotRequired[dict[str, Any] | None]


class ToolErrorResponse(TypedDict):
    error: Literal[True]
    error_type: str
    message: str
    retryable: bool
    suggestions: list[str]
    details: ToolErrorDetails


HTTP_STATUS_OK = 200
HTTP_STATUS_UNAUTHORIZED = 401
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_FORBIDDEN = 403
HTTP_STATUS_SERVER_ERROR = 500
HTTP_STATUS_BAD_REQUEST = 400

MCP_CODE_AUTH_FAILED = -32001
MCP_CODE_NOT_FOUND = -32002
MCP_CODE_FORBIDDEN = -32003
MCP_CODE_SERVER_ERROR = -32000
MCP_CODE_INVALID_PARAMS = -32602


ERROR_SUGGESTIONS: dict[str, list[str]] = {
    ERROR_TYPE_AUTH_FAILED: [
        "检查环境变量中的 Cookie 是否正确配置",
        "确认 _yapi_token 和 _yapi_uid 未过期",
        "尝试重新登录 YApi 获取新的 Cookie",
    ],
    ERROR_TYPE_RESOURCE_NOT_FOUND: [
        "检查 project_id、interface_id 或 catid 是否正确",
        "确认资源未被删除或移动",
        "尝试通过搜索功能查找正确的资源 ID",
    ],
    ERROR_TYPE_PERMISSION_DENIED: [
        "确认当前账号有访问该项目的权限",
        "联系项目管理员添加权限",
        "检查是否使用了正确的 Cookie",
    ],
    ERROR_TYPE_INVALID_PARAMS: [
        "检查传入参数的格式和类型是否正确",
        "确认必填参数（如 project_id、title、path、method）已提供",
        "参考接口文档确认参数要求",
    ],
    ERROR_TYPE_VALIDATION_FAILED: [
        "检查接口路径是否以 / 开头",
        "确认 HTTP method 是否为有效值（GET/POST/PUT/DELETE 等）",
        "检查 JSON 字符串格式是否正确",
    ],
    ERROR_TYPE_SERVER_ERROR: [
        "YApi 服务器可能暂时不可用，稍后重试",
        "检查 YApi 服务器状态和日志",
        "联系 YApi 管理员排查服务端问题",
    ],
    ERROR_TYPE_NETWORK_ERROR: [
        "检查网络连接是否正常",
        "确认 YAPI_SERVER_URL 配置正确",
        "检查防火墙或代理设置",
        "稍后重试",
    ],
    ERROR_TYPE_CONFIG_ERROR: [
        "检查环境变量配置是否完整",
        "确认 YAPI_SERVER_URL、YAPI_TOKEN、YAPI_UID 已设置",
        "参考项目 README 中的配置说明",
    ],
}


def get_error_suggestions(error_type: str) -> list[str]:
    return ERROR_SUGGESTIONS.get(error_type, ["请检查错误信息并重试"])


def format_tool_error(
    error_type: str,
    message: str,
    operation: str,
    params: dict[str, Any],
    error_code: int = -32000,
    retryable: bool = False,
    yapi_error: dict[str, Any] | None = None,
    suggestions: list[str] | None = None,
) -> str:
    response: ToolErrorResponse = {
        "error": True,
        "error_type": error_type,
        "message": message,
        "retryable": retryable,
        "suggestions": suggestions or get_error_suggestions(error_type),
        "details": {
            "operation": operation,
            "params": params,
            "error_code": error_code,
        },
    }

    if yapi_error is not None:
        response["details"]["yapi_error"] = yapi_error

    return json.dumps(response, ensure_ascii=False, indent=2)


class MCPError(Exception):
    """MCP protocol error with error code and optional data."""

    def __init__(
        self,
        code: int,
        message: str,
        data: ErrorData | None = None,
        error_type: str = ERROR_TYPE_SERVER_ERROR,
        retryable: bool = False,
    ) -> None:
        """Initialize MCP error.

        Args:
            code: MCP error code (negative integer)
            message: Human-readable error message
            data: Optional additional error data
            error_type: Error type constant for structured responses
            retryable: Whether this error is retryable
        """
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data
        self.error_type = error_type
        self.retryable = retryable

    def to_dict(self) -> dict[str, object]:
        """Convert to MCP error response dict."""
        result: dict[str, object] = {
            "code": self.code,
            "message": self.message,
            "error_type": self.error_type,
            "retryable": self.retryable,
        }
        if self.data is not None:
            result["data"] = self.data
        return result


def map_http_error_to_mcp(error: httpx.HTTPStatusError) -> MCPError:
    """Map HTTP status errors to MCP error codes.

    Error code mapping:
    - 200 with errcode != 0 → -32602 (YApi business error)
    - 401 Unauthorized → -32001 (Authentication failed)
    - 404 Not Found → -32002 (Resource not found)
    - 403 Forbidden → -32003 (Permission denied)
    - 500+ Server Error → -32000 (Server error)
    - 400 Bad Request → -32602 (Invalid params)
    - Other 4xx → -32602 (Invalid params)

    Args:
        error: httpx HTTPStatusError exception

    Returns:
        MCPError with appropriate code, message, error_type and retryable flag
    """
    status_code = error.response.status_code

    error_data: ErrorData = {"http_status": status_code}
    yapi_error: dict | None = None
    try:
        raw_error = error.response.json()
        if isinstance(raw_error, Mapping):
            yapi_error = dict(raw_error)
            error_data["yapi_error"] = yapi_error
    except Exception:
        error_data["response_text"] = error.response.text[:200]

    if status_code == HTTP_STATUS_OK and yapi_error and yapi_error.get("errcode", 0) != 0:
        errmsg = yapi_error.get("errmsg", "未知错误")
        message = (
            f"YApi 业务错误: {errmsg}。请检查传入的参数是否正确（如 catid、project_id、path 等）"
        )
        return MCPError(
            code=MCP_CODE_INVALID_PARAMS,
            message=message,
            data=error_data,
            error_type=ERROR_TYPE_INVALID_PARAMS,
            retryable=False,
        )

    if status_code == HTTP_STATUS_UNAUTHORIZED:
        return MCPError(
            code=MCP_CODE_AUTH_FAILED,
            message="认证失败: Cookie 无效或过期",
            data=error_data,
            error_type=ERROR_TYPE_AUTH_FAILED,
            retryable=False,
        )
    if status_code == HTTP_STATUS_NOT_FOUND:
        yapi_err = error_data.get("yapi_error")
        errmsg = (
            yapi_err.get("errmsg", "Resource not found")
            if isinstance(yapi_err, dict)
            else "Resource not found"
        )
        return MCPError(
            code=MCP_CODE_NOT_FOUND,
            message=f"资源不存在: {errmsg}",
            data=error_data,
            error_type=ERROR_TYPE_RESOURCE_NOT_FOUND,
            retryable=False,
        )
    if status_code == HTTP_STATUS_FORBIDDEN:
        return MCPError(
            code=MCP_CODE_FORBIDDEN,
            message="权限不足: 无法操作该项目/接口",
            data=error_data,
            error_type=ERROR_TYPE_PERMISSION_DENIED,
            retryable=False,
        )
    if status_code >= HTTP_STATUS_SERVER_ERROR:
        yapi_err = error_data.get("yapi_error")
        errmsg = (
            yapi_err.get("errmsg", "Internal server error")
            if isinstance(yapi_err, dict)
            else "Internal server error"
        )
        return MCPError(
            code=MCP_CODE_SERVER_ERROR,
            message=f"YApi 服务器错误: {errmsg}",
            data=error_data,
            error_type=ERROR_TYPE_SERVER_ERROR,
            retryable=True,
        )
    if status_code == HTTP_STATUS_BAD_REQUEST:
        yapi_err = error_data.get("yapi_error")
        errmsg = (
            yapi_err.get("errmsg", "Bad request") if isinstance(yapi_err, dict) else "Bad request"
        )
        return MCPError(
            code=MCP_CODE_INVALID_PARAMS,
            message=f"Invalid params: {errmsg}",
            data=error_data,
            error_type=ERROR_TYPE_INVALID_PARAMS,
            retryable=False,
        )
    return MCPError(
        code=MCP_CODE_INVALID_PARAMS,
        message=f"Invalid params: HTTP {status_code}",
        data=error_data,
        error_type=ERROR_TYPE_INVALID_PARAMS,
        retryable=False,
    )
