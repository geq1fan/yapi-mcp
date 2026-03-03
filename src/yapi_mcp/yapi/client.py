"""YApi API HTTP client implementation."""

import json
from typing import Any, NoReturn

import httpx
import markdown as md_lib

from .models import YApiErrorResponse, YApiInterface, YApiInterfaceSummary

# Markdown 转 HTML 转换器（单例）
_md_converter = md_lib.Markdown(extensions=["extra", "codehilite", "nl2br"])


def _markdown_to_html(text: str) -> str:
    """将 Markdown 文本转换为 HTML。

    Args:
        text: Markdown 格式文本

    Returns:
        HTML 格式文本
    """
    _md_converter.reset()
    return _md_converter.convert(text)


def _set_if_not_none(payload: dict[str, Any], key: str, value: Any) -> None:  # noqa: ANN401
    """Set payload key if value is not None."""
    if value is not None:
        payload[key] = value


def _set_json_if_not_none(payload: dict[str, Any], key: str, value: str | None) -> None:
    """Set payload key from JSON string if value is not None."""
    if value is not None:
        payload[key] = json.loads(value)


def _raise_yapi_api_error(response: httpx.Response, error: YApiErrorResponse) -> NoReturn:
    message = f"YApi API error: {error.errmsg} (code: {error.errcode})"
    raise httpx.HTTPStatusError(
        message,
        request=response.request,
        response=response,
    )


class YApiClient:
    """Async HTTP client for YApi API with cookie-based authentication."""

    def __init__(self, base_url: str, cookies: dict[str, str], timeout: float = 10.0) -> None:
        """Initialize YApi client.

        Args:
            base_url: YApi server base URL (e.g., "https://yapi.example.com")
            cookies: Authentication cookies dict with _yapi_token, _yapi_uid, ZYBIPSCAS
            timeout: Request timeout in seconds (default: 10.0)
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(
            base_url=f"{self.base_url}/api",
            cookies=cookies,
            timeout=timeout,
            follow_redirects=True,
        )

    async def __aenter__(self) -> "YApiClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Async context manager exit - close HTTP client."""
        await self.client.aclose()

    async def close(self) -> None:
        """Close the HTTP client connection."""
        await self.client.aclose()

    async def check_login_status(self) -> dict[str, Any]:
        """Validate credentials by calling GET /api/user/status."""
        response = await self.client.get("/user/status")
        self._check_response(response)
        data = response.json()
        return data.get("data", {})

    def _check_response(self, response: httpx.Response) -> None:
        """Check YApi API response for errors and raise appropriate exceptions.

        Args:
            response: httpx Response object

        Raises:
            httpx.HTTPStatusError: For HTTP-level errors (4xx, 5xx)
        """
        # First check HTTP status codes
        response.raise_for_status()

        # Then check YApi API-level errors (errcode != 0)
        try:
            data = response.json()
            if isinstance(data, dict) and "errcode" in data and data["errcode"] != 0:
                error = YApiErrorResponse(**data)
                # YApi returns errcode != 0 for business logic errors
                # Treat these as HTTP-equivalent errors
                _raise_yapi_api_error(response, error)
        except (ValueError, KeyError):
            # Not a JSON response or doesn't have errcode - proceed normally
            pass

    async def search_interfaces(
        self, project_id: int, keyword: str
    ) -> list[YApiInterfaceSummary]:
        """Search interfaces in a YApi project.

        使用 list_menu 接口获取项目下全量接口，突破 50 条限制。
        支持按接口标题、路径、描述、分类名进行搜索。

        Args:
            project_id: YApi project ID
            keyword: Search keyword (matches title, path, description, category name)

        Returns:
            List of matching interface summaries

        Raises:
            httpx.HTTPStatusError: For authentication, permission, or server errors
        """
        # 使用 list_menu 接口获取全量接口（无分页限制）
        response = await self.client.get(
            "/interface/list_menu",
            params={"project_id": project_id},
        )
        self._check_response(response)

        data = response.json()
        categories = data.get("data", [])

        # 展开树形结构为扁平列表，同时记录分类名
        interfaces: list[dict] = []
        for cat in categories:
            cat_name = cat.get("name", "")
            for iface in cat.get("list", []):
                # 将分类名注入到接口数据中，用于搜索
                iface["_cat_name"] = cat_name
                interfaces.append(iface)

        # 客户端关键词过滤（支持分类名搜索，同时匹配 desc 和 markdown）
        if keyword:
            keyword_lower = keyword.lower()
            interfaces = [
                iface
                for iface in interfaces
                if keyword_lower in iface.get("title", "").lower()
                or keyword_lower in iface.get("path", "").lower()
                or keyword_lower in iface.get("desc", "").lower()
                or keyword_lower in iface.get("markdown", "").lower()
                or keyword_lower in iface.get("_cat_name", "").lower()
            ]

        return [YApiInterfaceSummary(**iface) for iface in interfaces]

    async def get_interface(self, interface_id: int) -> YApiInterface:
        """Get complete interface definition by ID.

        Args:
            interface_id: YApi interface ID

        Returns:
            Complete interface definition

        Raises:
            httpx.HTTPStatusError: For authentication, not found, or server errors
        """
        response = await self.client.get("/interface/get", params={"id": interface_id})
        self._check_response(response)

        data = response.json()
        return YApiInterface(**data["data"])

    async def create_interface(
        self,
        project_id: int,
        catid: int,
        title: str,
        path: str,
        method: str,
        *,
        req_body: str = "",
        req_body_type: str | None = None,
        req_body_is_json_schema: bool | None = None,
        req_body_form: str = "",
        res_body: str = "",
        res_body_type: str | None = None,
        res_body_is_json_schema: bool | None = None,
        req_query: str = "",
        req_headers: str = "",
        req_params: str = "",
        markdown: str = "",
        status: str | None = None,
        tag: str = "",
        api_opened: bool | None = None,
    ) -> dict[str, Any]:
        """Create a new interface.

        Args:
            project_id: Project ID
            catid: Category ID
            title: Interface title
            path: Interface path (must start with /)
            method: HTTP method
            req_body: Request body (JSON Schema string)
            req_body_type: Request body type (form/json/raw/file)
            req_body_is_json_schema: Whether req_body is JSON Schema
            req_body_form: Form fields (JSON array: [{name, type, required, desc, example}])
            res_body: Response body (JSON Schema string)
            res_body_type: Response body type (json/raw)
            res_body_is_json_schema: Whether res_body is JSON Schema
            req_query: Query params (JSON array: [{name, required, desc, example}])
            req_headers: Request headers (JSON array: [{name, value, required, desc}])
            req_params: Path params (JSON array: [{name, example, desc}])
            markdown: Description in Markdown (auto-converted to HTML for desc)
            status: Interface status (undone/done)
            tag: Tags (JSON array: ["tag1", "tag2"])
            api_opened: Whether API is publicly accessible

        Returns:
            dict with keys: action ("created"), interface_id (int)
        """
        payload: dict[str, Any] = {
            "project_id": project_id,
            "catid": catid,
            "title": title,
            "path": path,
            "method": method.upper(),
        }

        if req_body:
            payload["req_body_other"] = req_body
            payload["req_body_type"] = req_body_type or "json"
            payload["req_body_is_json_schema"] = (
                req_body_is_json_schema if req_body_is_json_schema is not None else True
            )
        if req_body_form:
            payload["req_body_form"] = json.loads(req_body_form)
            if not req_body_type:
                payload["req_body_type"] = "form"
        if res_body:
            payload["res_body"] = res_body
            payload["res_body_type"] = res_body_type or "json"
            payload["res_body_is_json_schema"] = (
                res_body_is_json_schema if res_body_is_json_schema is not None else True
            )
        if req_query:
            payload["req_query"] = json.loads(req_query)
        if req_headers:
            payload["req_headers"] = json.loads(req_headers)
        if req_params:
            payload["req_params"] = json.loads(req_params)
        if markdown:
            payload["markdown"] = markdown
            payload["desc"] = _markdown_to_html(markdown)
        if status is not None:
            payload["status"] = status
        if tag:
            payload["tag"] = json.loads(tag)
        if api_opened is not None:
            payload["api_opened"] = api_opened

        response = await self.client.post("/interface/add", json=payload)
        self._check_response(response)

        data = response.json()
        return {"action": "created", "interface_id": int(data["data"]["_id"])}

    async def update_interface(
        self,
        interface_id: int,
        *,
        catid: int | None = None,
        title: str | None = None,
        path: str | None = None,
        method: str | None = None,
        req_body: str | None = None,
        req_body_type: str | None = None,
        req_body_is_json_schema: bool | None = None,
        req_body_form: str | None = None,
        res_body: str | None = None,
        res_body_type: str | None = None,
        res_body_is_json_schema: bool | None = None,
        req_query: str | None = None,
        req_headers: str | None = None,
        req_params: str | None = None,
        markdown: str | None = None,
        status: str | None = None,
        tag: str | None = None,
        api_opened: bool | None = None,
        switch_notice: bool | None = None,
        message: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing interface (read-before-write).

        Automatically fetches existing data and merges user-provided fields.
        Only fields explicitly passed will be updated; others keep their current values.

        Args:
            interface_id: Interface ID to update
            catid: Category ID (auto-fetched if not provided)
            title: Interface title
            path: Interface path (must start with /)
            method: HTTP method
            req_body: Request body (JSON Schema string)
            req_body_type: Request body type (form/json/raw/file)
            req_body_is_json_schema: Whether req_body is JSON Schema
            req_body_form: Form fields (JSON array: [{name, type, required, desc, example}])
            res_body: Response body (JSON Schema string)
            res_body_type: Response body type (json/raw)
            res_body_is_json_schema: Whether res_body is JSON Schema
            req_query: Query params (JSON array: [{name, required, desc, example}])
            req_headers: Request headers (JSON array: [{name, value, required, desc}])
            req_params: Path params (JSON array: [{name, example, desc}])
            markdown: Description in Markdown (auto-converted to HTML for desc)
            status: Interface status (undone/done)
            tag: Tags (JSON array: ["tag1", "tag2"])
            api_opened: Whether API is publicly accessible
            switch_notice: Whether to notify team members
            message: Change description

        Returns:
            dict with keys: action ("updated"), interface_id (int)
        """
        # 先读后写：获取现有接口数据
        existing = await self.get_interface(interface_id)

        payload: dict[str, Any] = {
            "id": interface_id,
            "catid": catid if catid is not None else existing.catid,
        }

        _set_if_not_none(payload, "title", title)
        _set_if_not_none(payload, "path", path)
        if method is not None:
            payload["method"] = method.upper()

        # 请求体参数
        _set_if_not_none(payload, "req_body_other", req_body)
        _set_if_not_none(payload, "req_body_type", req_body_type)
        _set_if_not_none(payload, "req_body_is_json_schema", req_body_is_json_schema)
        _set_json_if_not_none(payload, "req_body_form", req_body_form)

        # 响应体参数
        _set_if_not_none(payload, "res_body", res_body)
        _set_if_not_none(payload, "res_body_type", res_body_type)
        _set_if_not_none(payload, "res_body_is_json_schema", res_body_is_json_schema)

        # 数组参数
        _set_json_if_not_none(payload, "req_query", req_query)
        _set_json_if_not_none(payload, "req_headers", req_headers)
        _set_json_if_not_none(payload, "req_params", req_params)

        # 元数据参数
        if markdown is not None:
            payload["markdown"] = markdown
            payload["desc"] = _markdown_to_html(markdown) if markdown else ""
        _set_if_not_none(payload, "status", status)
        _set_json_if_not_none(payload, "tag", tag)
        _set_if_not_none(payload, "api_opened", api_opened)

        # 更新专有参数
        _set_if_not_none(payload, "switch_notice", switch_notice)
        _set_if_not_none(payload, "message", message)

        response = await self.client.post("/interface/up", json=payload)
        self._check_response(response)

        return {"action": "updated", "interface_id": interface_id}
