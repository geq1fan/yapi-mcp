"""Error handling tests for YApi client and MCP error mapping."""

import httpx
import pytest
import respx

from src.yapi.client import YApiClient
from src.yapi.errors import MCPError, map_http_error_to_mcp

BASE_URL = "https://yapi.example.com"

HTTP_UNAUTHORIZED = 401
HTTP_NOT_FOUND = 404
HTTP_FORBIDDEN = 403
HTTP_SERVER_ERROR = 500
HTTP_BAD_REQUEST = 400

MCP_CODE_AUTH_FAILED = -32001
MCP_CODE_NOT_FOUND = -32002
MCP_CODE_FORBIDDEN = -32003
MCP_CODE_SERVER_ERROR = -32000
MCP_CODE_INVALID_PARAMS = -32602


DEFAULT_TOKEN = "token"  # noqa: S105


def make_cookies(token: str) -> dict[str, str]:
    return {"_yapi_token": token, "_yapi_uid": "uid", "ZYBIPSCAS": "cas"}


@pytest.mark.asyncio
@respx.mock
async def test_authentication_failure_401() -> None:
    """Test 401 Unauthorized error handling."""
    cookies = make_cookies("invalid")

    respx.post(f"{BASE_URL}/api/interface/list").mock(
        return_value=httpx.Response(
            HTTP_UNAUTHORIZED,
            json={"errcode": HTTP_UNAUTHORIZED, "errmsg": "未登录"},
        )
    )

    async with YApiClient(BASE_URL, cookies) as client:
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.search_interfaces(project_id=1, keyword="test")

    # Map to MCP error
    mcp_error = map_http_error_to_mcp(exc_info.value)
    assert mcp_error.code == MCP_CODE_AUTH_FAILED
    assert "认证失败" in mcp_error.message
    assert mcp_error.data["http_status"] == HTTP_UNAUTHORIZED


@pytest.mark.asyncio
@respx.mock
async def test_resource_not_found_404() -> None:
    """Test 404 Not Found error handling."""
    cookies = make_cookies(DEFAULT_TOKEN)

    respx.get(f"{BASE_URL}/api/interface/get").mock(
        return_value=httpx.Response(
            HTTP_NOT_FOUND,
            json={"errcode": HTTP_NOT_FOUND, "errmsg": "接口不存在"},
        )
    )

    async with YApiClient(BASE_URL, cookies) as client:
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.get_interface(interface_id=99999)

    # Map to MCP error
    mcp_error = map_http_error_to_mcp(exc_info.value)
    assert mcp_error.code == MCP_CODE_NOT_FOUND
    assert "资源不存在" in mcp_error.message
    assert "接口不存在" in mcp_error.message


@pytest.mark.asyncio
@respx.mock
async def test_permission_denied_403() -> None:
    """Test 403 Forbidden error handling."""
    cookies = make_cookies(DEFAULT_TOKEN)

    respx.post(f"{BASE_URL}/api/interface/add").mock(
        return_value=httpx.Response(
            HTTP_FORBIDDEN,
            json={"errcode": HTTP_FORBIDDEN, "errmsg": "没有权限操作"},
        )
    )

    async with YApiClient(BASE_URL, cookies) as client:
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.create_interface(project_id=1, title="Test", path="/test", method="GET")

    # Map to MCP error
    mcp_error = map_http_error_to_mcp(exc_info.value)
    assert mcp_error.code == MCP_CODE_FORBIDDEN
    assert "权限不足" in mcp_error.message


@pytest.mark.asyncio
@respx.mock
async def test_server_error_500() -> None:
    """Test 500 Internal Server Error handling."""
    cookies = make_cookies(DEFAULT_TOKEN)

    respx.post(f"{BASE_URL}/api/interface/list").mock(
        return_value=httpx.Response(
            HTTP_SERVER_ERROR,
            json={"errcode": HTTP_SERVER_ERROR, "errmsg": "服务器内部错误"},
        )
    )

    async with YApiClient(BASE_URL, cookies) as client:
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.search_interfaces(project_id=1, keyword="test")

    # Map to MCP error
    mcp_error = map_http_error_to_mcp(exc_info.value)
    assert mcp_error.code == MCP_CODE_SERVER_ERROR
    assert "YApi 服务器错误" in mcp_error.message
    assert "服务器内部错误" in mcp_error.message


@pytest.mark.asyncio
@respx.mock
async def test_bad_request_400() -> None:
    """Test 400 Bad Request error handling."""
    cookies = make_cookies(DEFAULT_TOKEN)

    respx.post(f"{BASE_URL}/api/interface/add").mock(
        return_value=httpx.Response(
            HTTP_BAD_REQUEST,
            json={"errcode": HTTP_BAD_REQUEST, "errmsg": "参数错误"},
        )
    )

    async with YApiClient(BASE_URL, cookies) as client:
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.create_interface(project_id=1, title="", path="/test", method="GET")

    # Map to MCP error
    mcp_error = map_http_error_to_mcp(exc_info.value)
    assert mcp_error.code == MCP_CODE_INVALID_PARAMS
    assert "Invalid params" in mcp_error.message


def test_mcp_error_to_dict() -> None:
    """Test MCPError serialization to dict."""
    error = MCPError(
        code=MCP_CODE_AUTH_FAILED,
        message="Test error",
        data={"detail": "Additional info"},
    )

    error_dict = error.to_dict()
    assert error_dict["code"] == MCP_CODE_AUTH_FAILED
    assert error_dict["message"] == "Test error"
    assert error_dict["data"]["detail"] == "Additional info"


def test_mcp_error_without_data() -> None:
    """Test MCPError without optional data field."""
    error = MCPError(code=MCP_CODE_SERVER_ERROR, message="Simple error")

    error_dict = error.to_dict()
    assert error_dict["code"] == MCP_CODE_SERVER_ERROR
    assert error_dict["message"] == "Simple error"
    assert "data" not in error_dict
