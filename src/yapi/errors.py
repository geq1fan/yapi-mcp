"""Error mapping from YApi/HTTP errors to MCP errors."""

from collections.abc import Mapping, MutableMapping

import httpx

ErrorData = MutableMapping[str, object]

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


class MCPError(Exception):
    """MCP protocol error with error code and optional data."""

    def __init__(
        self,
        code: int,
        message: str,
        data: ErrorData | None = None,
    ) -> None:
        """Initialize MCP error.

        Args:
            code: MCP error code (negative integer)
            message: Human-readable error message
            data: Optional additional error data
        """
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data

    def to_dict(self) -> dict[str, object]:
        """Convert to MCP error response dict."""
        result: dict[str, object] = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result


def map_http_error_to_mcp(error: httpx.HTTPStatusError) -> MCPError:
    """Map HTTP status errors to MCP error codes.

    Error code mapping:
    - 401 Unauthorized → -32001 (Authentication failed)
    - 404 Not Found → -32002 (Resource not found)
    - 403 Forbidden → -32003 (Permission denied)
    - 500+ Server Error → -32000 (Server error)
    - 400 Bad Request → -32602 (Invalid params)
    - Other 4xx → -32602 (Invalid params)

    Args:
        error: httpx HTTPStatusError exception

    Returns:
        MCPError with appropriate code and message
    """
    status_code = error.response.status_code

    # Try to extract YApi error details from response
    error_data: ErrorData = {"http_status": status_code}
    try:
        yapi_error = error.response.json()
        if isinstance(yapi_error, Mapping):
            error_data["yapi_error"] = dict(yapi_error)
    except Exception:
        # If response is not JSON, include response text
        error_data["response_text"] = error.response.text[:200]

    # Map HTTP status codes to MCP error codes
    if status_code == HTTP_STATUS_UNAUTHORIZED:
        return MCPError(
            code=MCP_CODE_AUTH_FAILED,
            message="认证失败: Cookie 无效或过期",
            data=error_data,
        )
    if status_code == HTTP_STATUS_NOT_FOUND:
        errmsg = error_data.get("yapi_error", {}).get("errmsg", "Resource not found")
        return MCPError(
            code=MCP_CODE_NOT_FOUND,
            message=f"资源不存在: {errmsg}",
            data=error_data,
        )
    if status_code == HTTP_STATUS_FORBIDDEN:
        return MCPError(
            code=MCP_CODE_FORBIDDEN,
            message="权限不足: 无法操作该项目/接口",
            data=error_data,
        )
    if status_code >= HTTP_STATUS_SERVER_ERROR:
        errmsg = error_data.get("yapi_error", {}).get("errmsg", "Internal server error")
        return MCPError(
            code=MCP_CODE_SERVER_ERROR,
            message=f"YApi 服务器错误: {errmsg}",
            data=error_data,
        )
    if status_code == HTTP_STATUS_BAD_REQUEST:
        errmsg = error_data.get("yapi_error", {}).get("errmsg", "Bad request")
        return MCPError(
            code=MCP_CODE_INVALID_PARAMS,
            message=f"Invalid params: {errmsg}",
            data=error_data,
        )
    # Other 4xx errors
    return MCPError(
        code=MCP_CODE_INVALID_PARAMS,
        message=f"Invalid params: HTTP {status_code}",
        data=error_data,
    )
