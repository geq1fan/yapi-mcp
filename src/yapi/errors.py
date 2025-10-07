"""Error mapping from YApi/HTTP errors to MCP errors."""

from typing import Any

import httpx


class MCPError(Exception):
    """MCP protocol error with error code and optional data."""

    def __init__(self, code: int, message: str, data: Any = None) -> None:
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

    def to_dict(self) -> dict[str, Any]:
        """Convert to MCP error response dict."""
        result: dict[str, Any] = {"code": self.code, "message": self.message}
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
    error_data: dict[str, Any] = {"http_status": status_code}
    try:
        yapi_error = error.response.json()
        if isinstance(yapi_error, dict):
            error_data["yapi_error"] = yapi_error
    except Exception:
        # If response is not JSON, include response text
        error_data["response_text"] = error.response.text[:200]

    # Map HTTP status codes to MCP error codes
    if status_code == 401:
        return MCPError(
            code=-32001,
            message="认证失败: Cookie 无效或过期",
            data=error_data,
        )
    if status_code == 404:
        return MCPError(
            code=-32002,
            message=f"资源不存在: {error_data.get('yapi_error', {}).get('errmsg', 'Resource not found')}",
            data=error_data,
        )
    if status_code == 403:
        return MCPError(
            code=-32003,
            message="权限不足: 无法操作该项目/接口",
            data=error_data,
        )
    if status_code >= 500:
        return MCPError(
            code=-32000,
            message=f"YApi 服务器错误: {error_data.get('yapi_error', {}).get('errmsg', 'Internal server error')}",
            data=error_data,
        )
    if status_code == 400:
        return MCPError(
            code=-32602,
            message=f"Invalid params: {error_data.get('yapi_error', {}).get('errmsg', 'Bad request')}",
            data=error_data,
        )
    # Other 4xx errors
    return MCPError(
        code=-32602,
        message=f"Invalid params: HTTP {status_code}",
        data=error_data,
    )
