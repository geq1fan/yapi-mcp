"""Integration tests for YApiClient with mocked HTTP responses."""

import json

import httpx
import pytest
import respx

from conftest import make_cookies
from yapi_mcp.yapi.client import YApiClient
from yapi_mcp.yapi.models import YApiInterface, YApiInterfaceSummary

BASE_URL = "https://yapi.example.com"
DEFAULT_TOKEN = "token"  # noqa: S105
SEARCH_RESULT_COUNT = 2
DEFAULT_INTERFACE_ID = 123
CREATED_INTERFACE_ID = 789


@pytest.mark.asyncio
@respx.mock
async def test_search_interfaces_success() -> None:
    """Test successful interface search with mocked YApi API."""
    cookies = make_cookies(DEFAULT_TOKEN)

    # Mock YApi API response - 使用 list_menu 接口（树形结构）
    respx.get(f"{BASE_URL}/api/interface/list_menu").mock(
        return_value=httpx.Response(
            200,
            json={
                "errcode": 0,
                "data": [
                    {
                        "_id": 100,
                        "name": "用户模块",
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
                        ],
                    }
                ],
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
async def test_search_interfaces_returns_all() -> None:
    """Test search returns all interfaces without limit (using list_menu)."""
    cookies = make_cookies(DEFAULT_TOKEN)

    # Mock response with 100 items across multiple categories
    mock_interfaces_cat1 = [
        {"_id": i, "title": f"接口{i}", "path": f"/api/{i}", "method": "GET"} for i in range(60)
    ]
    mock_interfaces_cat2 = [
        {"_id": i, "title": f"接口{i}", "path": f"/api/{i}", "method": "GET"} for i in range(60, 100)
    ]

    respx.get(f"{BASE_URL}/api/interface/list_menu").mock(
        return_value=httpx.Response(
            200,
            json={
                "errcode": 0,
                "data": [
                    {"_id": 1, "name": "分类1", "list": mock_interfaces_cat1},
                    {"_id": 2, "name": "分类2", "list": mock_interfaces_cat2},
                ],
            },
        )
    )

    async with YApiClient(BASE_URL, cookies) as client:
        results = await client.search_interfaces(project_id=1, keyword="接口")

    # Should return all 100 items (no 50 limit)
    assert len(results) == 100


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
                    "catid": 100,
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
    """Test successful interface creation via create_interface."""
    cookies = make_cookies(DEFAULT_TOKEN)

    respx.post(f"{BASE_URL}/api/interface/add").mock(
        return_value=httpx.Response(
            200,
            json={"errcode": 0, "data": {"_id": CREATED_INTERFACE_ID}},
        )
    )

    async with YApiClient(BASE_URL, cookies) as client:
        result = await client.create_interface(
            project_id=1,
            catid=100,
            title="测试接口",
            path="/api/test",
            method="GET",
        )

    assert result["action"] == "created"
    assert result["interface_id"] == CREATED_INTERFACE_ID


@pytest.mark.asyncio
@respx.mock
async def test_create_interface_with_new_params() -> None:
    """Test create_interface with req_headers, req_params, status, tag."""
    cookies = make_cookies(DEFAULT_TOKEN)

    add_route = respx.post(f"{BASE_URL}/api/interface/add").mock(
        return_value=httpx.Response(
            200,
            json={"errcode": 0, "data": {"_id": CREATED_INTERFACE_ID}},
        )
    )

    async with YApiClient(BASE_URL, cookies) as client:
        await client.create_interface(
            project_id=1,
            catid=100,
            title="带完整参数的接口",
            path="/api/users/:id",
            method="POST",
            req_headers='[{"name":"Authorization","value":"Bearer token","required":"1"}]',
            req_params='[{"name":"id","example":"123","desc":"用户ID"}]',
            req_query='[{"name":"page","required":"0","desc":"页码"}]',
            status="undone",
            tag='["v2","auth"]',
        )

    # Verify payload sent to YApi
    sent_payload = json.loads(add_route.calls[0].request.content)
    assert sent_payload["req_headers"] == [
        {"name": "Authorization", "value": "Bearer token", "required": "1"}
    ]
    assert sent_payload["req_params"] == [{"name": "id", "example": "123", "desc": "用户ID"}]
    assert sent_payload["req_query"] == [{"name": "page", "required": "0", "desc": "页码"}]
    assert sent_payload["status"] == "undone"
    assert sent_payload["tag"] == ["v2", "auth"]


@pytest.mark.asyncio
@respx.mock
async def test_update_interface_success() -> None:
    """Test successful interface update via update_interface."""
    cookies = make_cookies(DEFAULT_TOKEN)

    # Mock GET for read-before-write
    respx.get(f"{BASE_URL}/api/interface/get").mock(
        return_value=httpx.Response(
            200,
            json={
                "errcode": 0,
                "data": {
                    "_id": DEFAULT_INTERFACE_ID,
                    "title": "原始标题",
                    "path": "/api/old",
                    "method": "GET",
                    "project_id": 1,
                    "catid": 100,
                },
            },
        )
    )

    respx.post(f"{BASE_URL}/api/interface/up").mock(
        return_value=httpx.Response(
            200,
            json={"errcode": 0, "data": {}},
        )
    )

    async with YApiClient(BASE_URL, cookies) as client:
        result = await client.update_interface(
            interface_id=DEFAULT_INTERFACE_ID,
            title="更新的标题",
        )

    assert result["action"] == "updated"
    assert result["interface_id"] == DEFAULT_INTERFACE_ID


EXISTING_CATID = 200


@pytest.mark.asyncio
@respx.mock
async def test_update_interface_auto_catid() -> None:
    """Test update_interface auto-fetches catid from existing interface."""
    cookies = make_cookies(DEFAULT_TOKEN)

    # Mock GET - existing interface with catid=200
    respx.get(f"{BASE_URL}/api/interface/get").mock(
        return_value=httpx.Response(
            200,
            json={
                "errcode": 0,
                "data": {
                    "_id": DEFAULT_INTERFACE_ID,
                    "title": "原始标题",
                    "path": "/api/test",
                    "method": "GET",
                    "project_id": 1,
                    "catid": EXISTING_CATID,
                },
            },
        )
    )

    up_route = respx.post(f"{BASE_URL}/api/interface/up").mock(
        return_value=httpx.Response(
            200,
            json={"errcode": 0, "data": {}},
        )
    )

    async with YApiClient(BASE_URL, cookies) as client:
        await client.update_interface(
            interface_id=DEFAULT_INTERFACE_ID,
            title="新标题",
            # catid not provided - should use existing value 200
        )

    # Verify catid was auto-filled from existing data
    sent_payload = json.loads(up_route.calls[0].request.content)
    assert sent_payload["catid"] == EXISTING_CATID
    assert sent_payload["title"] == "新标题"


@pytest.mark.asyncio
@respx.mock
async def test_yapi_api_error_with_errcode() -> None:
    """Test YApi API error response (errcode != 0)."""
    cookies = make_cookies(DEFAULT_TOKEN)

    # YApi returns 200 but with errcode != 0 for business errors
    respx.get(f"{BASE_URL}/api/interface/list_menu").mock(
        return_value=httpx.Response(
            200,
            json={"errcode": 400, "errmsg": "项目不存在"},
        )
    )

    async with YApiClient(BASE_URL, cookies) as client:
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.search_interfaces(project_id=99999, keyword="test")

    assert "项目不存在" in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
async def test_check_login_status_success() -> None:
    """Test successful credential validation via /api/user/status."""
    cookies = make_cookies(DEFAULT_TOKEN)

    respx.get(f"{BASE_URL}/api/user/status").mock(
        return_value=httpx.Response(
            200,
            json={"errcode": 0, "data": {"username": "testuser", "email": "test@example.com", "role": "member"}},
        )
    )

    async with YApiClient(BASE_URL, cookies) as client:
        user_info = await client.check_login_status()

    assert user_info["username"] == "testuser"


@pytest.mark.asyncio
@respx.mock
async def test_check_login_status_auth_failure() -> None:
    """Test credential validation with HTTP 401 raises HTTPStatusError."""
    cookies = make_cookies("expired_token")

    respx.get(f"{BASE_URL}/api/user/status").mock(
        return_value=httpx.Response(401)
    )

    async with YApiClient(BASE_URL, cookies) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await client.check_login_status()


@pytest.mark.asyncio
@respx.mock
async def test_check_login_status_errcode_nonzero() -> None:
    """Test credential validation with errcode != 0 raises HTTPStatusError."""
    cookies = make_cookies(DEFAULT_TOKEN)

    respx.get(f"{BASE_URL}/api/user/status").mock(
        return_value=httpx.Response(
            200,
            json={"errcode": 40011, "errmsg": "用户未登录"},
        )
    )

    async with YApiClient(BASE_URL, cookies) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await client.check_login_status()
