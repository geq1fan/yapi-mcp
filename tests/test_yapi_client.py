"""Integration tests for YApiClient with mocked HTTP responses."""

import httpx
import pytest
import respx

from src.yapi.client import YApiClient
from src.yapi.models import YApiInterface, YApiInterfaceSummary

BASE_URL = "https://yapi.example.com"
DEFAULT_TOKEN = "token"  # noqa: S105
SEARCH_RESULT_COUNT = 2
DEFAULT_INTERFACE_ID = 123
RESULT_LIMIT = 50
CREATED_INTERFACE_ID = 789


def make_cookies(token: str) -> dict[str, str]:
    return {"_yapi_token": token, "_yapi_uid": "uid", "ZYBIPSCAS": "cas"}


@pytest.mark.asyncio
@respx.mock
async def test_search_interfaces_success() -> None:
    """Test successful interface search with mocked YApi API."""
    cookies = make_cookies(DEFAULT_TOKEN)

    # Mock YApi API response
    respx.post(f"{BASE_URL}/api/interface/list").mock(
        return_value=httpx.Response(
            200,
            json={
                "errcode": 0,
                "data": {
                    "list": [
                        {
                            "_id": DEFAULT_INTERFACE_ID,
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

    async with YApiClient(BASE_URL, cookies) as client:
        results = await client.search_interfaces(project_id=1, keyword="用户")

    assert len(results) == SEARCH_RESULT_COUNT
    assert isinstance(results[0], YApiInterfaceSummary)
    assert results[0].id == DEFAULT_INTERFACE_ID
    assert results[0].title == "用户登录"


@pytest.mark.asyncio
@respx.mock
async def test_search_interfaces_limit_50() -> None:
    """Test search results are limited to 50 items."""
    cookies = make_cookies(DEFAULT_TOKEN)

    # Mock response with 100 items
    mock_interfaces = [
        {"_id": i, "title": f"接口{i}", "path": f"/api/{i}", "method": "GET"} for i in range(100)
    ]

    respx.post(f"{BASE_URL}/api/interface/list").mock(
        return_value=httpx.Response(
            200,
            json={"errcode": 0, "data": {"list": mock_interfaces}},
        )
    )

    async with YApiClient(BASE_URL, cookies) as client:
        results = await client.search_interfaces(project_id=1, keyword="接口")

    # Should be limited to 50
    assert len(results) == RESULT_LIMIT


@pytest.mark.asyncio
@respx.mock
async def test_get_interface_success() -> None:
    """Test successful interface retrieval."""
    cookies = make_cookies(DEFAULT_TOKEN)

    respx.get(f"{BASE_URL}/api/interface/get").mock(
        return_value=httpx.Response(
            200,
            json={
                "errcode": 0,
                "data": {
                    "_id": DEFAULT_INTERFACE_ID,
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

    async with YApiClient(BASE_URL, cookies) as client:
        interface = await client.get_interface(interface_id=123)

    assert isinstance(interface, YApiInterface)
    assert interface.id == DEFAULT_INTERFACE_ID
    assert interface.title == "用户登录"
    assert interface.method == "POST"


@pytest.mark.asyncio
@respx.mock
async def test_create_interface_success() -> None:
    """Test successful interface creation."""
    cookies = make_cookies(DEFAULT_TOKEN)

    respx.post(f"{BASE_URL}/api/interface/add").mock(
        return_value=httpx.Response(
            200,
            json={"errcode": 0, "data": {"_id": CREATED_INTERFACE_ID}},
        )
    )

    async with YApiClient(BASE_URL, cookies) as client:
        interface_id = await client.create_interface(
            project_id=1,
            title="测试接口",
            path="/api/test",
            method="GET",
        )

    assert interface_id == CREATED_INTERFACE_ID


@pytest.mark.asyncio
@respx.mock
async def test_update_interface_success() -> None:
    """Test successful interface update."""
    cookies = make_cookies(DEFAULT_TOKEN)

    respx.post(f"{BASE_URL}/api/interface/up").mock(
        return_value=httpx.Response(
            200,
            json={"errcode": 0, "data": {}},
        )
    )

    async with YApiClient(BASE_URL, cookies) as client:
        success = await client.update_interface(
            interface_id=DEFAULT_INTERFACE_ID,
            title="更新的标题",
        )

    assert success is True


@pytest.mark.asyncio
@respx.mock
async def test_yapi_api_error_with_errcode() -> None:
    """Test YApi API error response (errcode != 0)."""
    cookies = make_cookies(DEFAULT_TOKEN)

    # YApi returns 200 but with errcode != 0 for business errors
    respx.post(f"{BASE_URL}/api/interface/list").mock(
        return_value=httpx.Response(
            200,
            json={"errcode": 400, "errmsg": "项目不存在"},
        )
    )

    async with YApiClient(BASE_URL, cookies) as client:
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.search_interfaces(project_id=99999, keyword="test")

    assert "项目不存在" in str(exc_info.value)
