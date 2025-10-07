"""Integration tests for YApiClient with mocked HTTP responses."""

import httpx
import pytest
import respx

from src.yapi.client import YApiClient
from src.yapi.models import YApiInterface, YApiInterfaceSummary


@pytest.mark.asyncio
@respx.mock
async def test_search_interfaces_success():
    """Test successful interface search with mocked YApi API."""
    base_url = "https://yapi.example.com"
    cookies = {"_yapi_token": "token", "_yapi_uid": "uid", "ZYBIPSCAS": "cas"}

    # Mock YApi API response
    respx.post(f"{base_url}/api/interface/list").mock(
        return_value=httpx.Response(
            200,
            json={
                "errcode": 0,
                "data": {
                    "list": [
                        {
                            "_id": 123,
                            "title": "用户登录",
                            "path": "/api/login",
                            "method": "POST",
                        },
                        {
                            "_id": 456,
                            "title": "用户注册",
                            "path": "/api/register",
                            "method": "POST",
                        },
                    ]
                },
            },
        )
    )

    async with YApiClient(base_url, cookies) as client:
        results = await client.search_interfaces(project_id=1, keyword="用户")

    assert len(results) == 2
    assert isinstance(results[0], YApiInterfaceSummary)
    assert results[0].id == 123
    assert results[0].title == "用户登录"


@pytest.mark.asyncio
@respx.mock
async def test_search_interfaces_limit_50():
    """Test search results are limited to 50 items."""
    base_url = "https://yapi.example.com"
    cookies = {"_yapi_token": "token", "_yapi_uid": "uid", "ZYBIPSCAS": "cas"}

    # Mock response with 100 items
    mock_interfaces = [
        {"_id": i, "title": f"接口{i}", "path": f"/api/{i}", "method": "GET"} for i in range(100)
    ]

    respx.post(f"{base_url}/api/interface/list").mock(
        return_value=httpx.Response(
            200,
            json={"errcode": 0, "data": {"list": mock_interfaces}},
        )
    )

    async with YApiClient(base_url, cookies) as client:
        results = await client.search_interfaces(project_id=1, keyword="接口")

    # Should be limited to 50
    assert len(results) == 50


@pytest.mark.asyncio
@respx.mock
async def test_get_interface_success():
    """Test successful interface retrieval."""
    base_url = "https://yapi.example.com"
    cookies = {"_yapi_token": "token", "_yapi_uid": "uid", "ZYBIPSCAS": "cas"}

    respx.get(f"{base_url}/api/interface/get").mock(
        return_value=httpx.Response(
            200,
            json={
                "errcode": 0,
                "data": {
                    "_id": 123,
                    "title": "用户登录",
                    "path": "/api/login",
                    "method": "POST",
                    "project_id": 1,
                    "desc": "用户登录接口",
                    "req_body_other": '{"username": "string", "password": "string"}',
                    "res_body": '{"token": "string"}',
                },
            },
        )
    )

    async with YApiClient(base_url, cookies) as client:
        interface = await client.get_interface(interface_id=123)

    assert isinstance(interface, YApiInterface)
    assert interface.id == 123
    assert interface.title == "用户登录"
    assert interface.method == "POST"


@pytest.mark.asyncio
@respx.mock
async def test_create_interface_success():
    """Test successful interface creation."""
    base_url = "https://yapi.example.com"
    cookies = {"_yapi_token": "token", "_yapi_uid": "uid", "ZYBIPSCAS": "cas"}

    respx.post(f"{base_url}/api/interface/add").mock(
        return_value=httpx.Response(
            200,
            json={"errcode": 0, "data": {"_id": 789}},
        )
    )

    async with YApiClient(base_url, cookies) as client:
        interface_id = await client.create_interface(
            project_id=1,
            title="测试接口",
            path="/api/test",
            method="GET",
        )

    assert interface_id == 789


@pytest.mark.asyncio
@respx.mock
async def test_update_interface_success():
    """Test successful interface update."""
    base_url = "https://yapi.example.com"
    cookies = {"_yapi_token": "token", "_yapi_uid": "uid", "ZYBIPSCAS": "cas"}

    respx.post(f"{base_url}/api/interface/up").mock(
        return_value=httpx.Response(
            200,
            json={"errcode": 0, "data": {}},
        )
    )

    async with YApiClient(base_url, cookies) as client:
        success = await client.update_interface(
            interface_id=123,
            title="更新的标题",
        )

    assert success is True


@pytest.mark.asyncio
@respx.mock
async def test_yapi_api_error_with_errcode():
    """Test YApi API error response (errcode != 0)."""
    base_url = "https://yapi.example.com"
    cookies = {"_yapi_token": "token", "_yapi_uid": "uid", "ZYBIPSCAS": "cas"}

    # YApi returns 200 but with errcode != 0 for business errors
    respx.post(f"{base_url}/api/interface/list").mock(
        return_value=httpx.Response(
            200,
            json={"errcode": 400, "errmsg": "项目不存在"},
        )
    )

    async with YApiClient(base_url, cookies) as client:
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.search_interfaces(project_id=99999, keyword="test")

    assert "项目不存在" in str(exc_info.value)
