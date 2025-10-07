"""Error handling tests for YApi client and MCP error mapping."""

import httpx
import pytest
import respx

from src.yapi.client import YApiClient
from src.yapi.errors import MCPError, map_http_error_to_mcp


@pytest.mark.asyncio
@respx.mock
async def test_authentication_failure_401():
    """Test 401 Unauthorized error handling."""
    base_url = "https://yapi.example.com"
    cookies = {"_yapi_token": "invalid", "_yapi_uid": "uid", "ZYBIPSCAS": "cas"}

    respx.post(f"{base_url}/api/interface/list").mock(
        return_value=httpx.Response(401, json={"errcode": 401, "errmsg": "未登录"})
    )

    async with YApiClient(base_url, cookies) as client:
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.search_interfaces(project_id=1, keyword="test")

    # Map to MCP error
    mcp_error = map_http_error_to_mcp(exc_info.value)
    assert mcp_error.code == -32001
    assert "认证失败" in mcp_error.message
    assert mcp_error.data["http_status"] == 401


@pytest.mark.asyncio
@respx.mock
async def test_resource_not_found_404():
    """Test 404 Not Found error handling."""
    base_url = "https://yapi.example.com"
    cookies = {"_yapi_token": "token", "_yapi_uid": "uid", "ZYBIPSCAS": "cas"}

    respx.get(f"{base_url}/api/interface/get").mock(
        return_value=httpx.Response(404, json={"errcode": 404, "errmsg": "接口不存在"})
    )

    async with YApiClient(base_url, cookies) as client:
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.get_interface(interface_id=99999)

    # Map to MCP error
    mcp_error = map_http_error_to_mcp(exc_info.value)
    assert mcp_error.code == -32002
    assert "资源不存在" in mcp_error.message
    assert "接口不存在" in mcp_error.message


@pytest.mark.asyncio
@respx.mock
async def test_permission_denied_403():
    """Test 403 Forbidden error handling."""
    base_url = "https://yapi.example.com"
    cookies = {"_yapi_token": "token", "_yapi_uid": "uid", "ZYBIPSCAS": "cas"}

    respx.post(f"{base_url}/api/interface/add").mock(
        return_value=httpx.Response(403, json={"errcode": 403, "errmsg": "没有权限操作"})
    )

    async with YApiClient(base_url, cookies) as client:
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.create_interface(project_id=1, title="Test", path="/test", method="GET")

    # Map to MCP error
    mcp_error = map_http_error_to_mcp(exc_info.value)
    assert mcp_error.code == -32003
    assert "权限不足" in mcp_error.message


@pytest.mark.asyncio
@respx.mock
async def test_server_error_500():
    """Test 500 Internal Server Error handling."""
    base_url = "https://yapi.example.com"
    cookies = {"_yapi_token": "token", "_yapi_uid": "uid", "ZYBIPSCAS": "cas"}

    respx.post(f"{base_url}/api/interface/list").mock(
        return_value=httpx.Response(500, json={"errcode": 500, "errmsg": "服务器内部错误"})
    )

    async with YApiClient(base_url, cookies) as client:
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.search_interfaces(project_id=1, keyword="test")

    # Map to MCP error
    mcp_error = map_http_error_to_mcp(exc_info.value)
    assert mcp_error.code == -32000
    assert "YApi 服务器错误" in mcp_error.message
    assert "服务器内部错误" in mcp_error.message


@pytest.mark.asyncio
@respx.mock
async def test_bad_request_400():
    """Test 400 Bad Request error handling."""
    base_url = "https://yapi.example.com"
    cookies = {"_yapi_token": "token", "_yapi_uid": "uid", "ZYBIPSCAS": "cas"}

    respx.post(f"{base_url}/api/interface/add").mock(
        return_value=httpx.Response(400, json={"errcode": 400, "errmsg": "参数错误"})
    )

    async with YApiClient(base_url, cookies) as client:
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.create_interface(project_id=1, title="", path="/test", method="GET")

    # Map to MCP error
    mcp_error = map_http_error_to_mcp(exc_info.value)
    assert mcp_error.code == -32602
    assert "Invalid params" in mcp_error.message


def test_mcp_error_to_dict():
    """Test MCPError serialization to dict."""
    error = MCPError(
        code=-32001,
        message="Test error",
        data={"detail": "Additional info"},
    )

    error_dict = error.to_dict()
    assert error_dict["code"] == -32001
    assert error_dict["message"] == "Test error"
    assert error_dict["data"]["detail"] == "Additional info"


def test_mcp_error_without_data():
    """Test MCPError without optional data field."""
    error = MCPError(code=-32000, message="Simple error")

    error_dict = error.to_dict()
    assert error_dict["code"] == -32000
    assert error_dict["message"] == "Simple error"
    assert "data" not in error_dict
