"""YApi API HTTP client implementation."""

from typing import Any, NoReturn

import httpx

from .models import YApiErrorResponse, YApiInterface, YApiInterfaceSummary


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

        # 客户端关键词过滤（支持分类名搜索）
        if keyword:
            keyword_lower = keyword.lower()
            interfaces = [
                iface
                for iface in interfaces
                if keyword_lower in iface.get("title", "").lower()
                or keyword_lower in iface.get("path", "").lower()
                or keyword_lower in iface.get("desc", "").lower()
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

    async def save_interface(
        self,
        catid: int,
        project_id: int | None = None,
        interface_id: int | None = None,
        title: str | None = None,
        path: str | None = None,
        method: str | None = None,
        req_body: str = "",
        res_body: str = "",
        desc: str = "",
        req_body_type: str | None = None,
        req_body_is_json_schema: bool | None = None,
        res_body_type: str | None = None,
        res_body_is_json_schema: bool | None = None,
    ) -> dict[str, Any]:
        """Save interface definition (create or update).

        If interface_id is provided, update the existing interface.
        If interface_id is not provided, create a new interface.

        Args:
            catid: Category ID (required for both create and update)
            project_id: Project ID (required for create)
            interface_id: Interface ID (if provided, update; otherwise create)
            title: Interface title (required for create)
            path: Interface path, must start with / (required for create)
            method: HTTP method (required for create)
            req_body: Request body definition (JSON string, optional)
            res_body: Response body definition (JSON string, optional)
            desc: Interface description (optional)
            req_body_type: Request body type (form, json, raw, file)
            req_body_is_json_schema: Whether req_body is JSON Schema format
            res_body_type: Response body type (json, raw)
            res_body_is_json_schema: Whether res_body is JSON Schema format

        Returns:
            dict with keys: action ("created" or "updated"), interface_id (int)

        Raises:
            ValueError: When required parameters are missing for create mode
            httpx.HTTPStatusError: For validation, permission, or server errors
        """
        if interface_id is None:
            # 创建模式：校验必填参数
            missing = []
            if project_id is None:
                missing.append("project_id")
            if title is None:
                missing.append("title")
            if path is None:
                missing.append("path")
            if method is None:
                missing.append("method")
            if missing:
                msg = f"创建接口需要以下参数: {', '.join(missing)}"
                raise ValueError(msg)

            # 调用创建 API
            payload: dict[str, Any] = {
                "project_id": project_id,
                "catid": catid,
                "title": title,
                "path": path,
                "method": method.upper(),  # type: ignore[union-attr]
            }

            if req_body:
                payload["req_body_other"] = req_body
                payload["req_body_type"] = req_body_type if req_body_type else "json"
                payload["req_body_is_json_schema"] = (
                    req_body_is_json_schema if req_body_is_json_schema is not None else True
                )
            if res_body:
                payload["res_body"] = res_body
                payload["res_body_type"] = res_body_type if res_body_type else "json"
                payload["res_body_is_json_schema"] = (
                    res_body_is_json_schema if res_body_is_json_schema is not None else True
                )
            if desc:
                payload["desc"] = desc

            response = await self.client.post("/interface/add", json=payload)
            self._check_response(response)

            data = response.json()
            return {"action": "created", "interface_id": int(data["data"]["_id"])}

        # 更新模式
        payload = {"id": interface_id, "catid": catid}

        if title is not None:
            payload["title"] = title
        if path is not None:
            payload["path"] = path
        if method is not None:
            payload["method"] = method.upper()
        if req_body:
            payload["req_body_other"] = req_body
        if res_body:
            payload["res_body"] = res_body
        if desc is not None:
            payload["desc"] = desc
        # 类型标记参数独立设置（不依赖内容参数）
        if req_body_type is not None:
            payload["req_body_type"] = req_body_type
        if req_body_is_json_schema is not None:
            payload["req_body_is_json_schema"] = req_body_is_json_schema
        if res_body_type is not None:
            payload["res_body_type"] = res_body_type
        if res_body_is_json_schema is not None:
            payload["res_body_is_json_schema"] = res_body_is_json_schema

        response = await self.client.post("/interface/up", json=payload)
        self._check_response(response)

        return {"action": "updated", "interface_id": interface_id}
