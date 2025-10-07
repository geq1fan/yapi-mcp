"""YApi API HTTP client implementation."""

from typing import Any

import httpx

from .models import YApiErrorResponse, YApiInterface, YApiInterfaceSummary


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
                raise httpx.HTTPStatusError(
                    f"YApi API error: {error.errmsg} (code: {error.errcode})",
                    request=response.request,
                    response=response,
                )
        except (ValueError, KeyError):
            # Not a JSON response or doesn't have errcode - proceed normally
            pass

    async def search_interfaces(self, project_id: int, keyword: str) -> list[YApiInterfaceSummary]:
        """Search interfaces in a YApi project.

        Args:
            project_id: YApi project ID
            keyword: Search keyword (matches title, path, description)

        Returns:
            List of interface summaries (max 50 results)

        Raises:
            httpx.HTTPStatusError: For authentication, permission, or server errors
        """
        response = await self.client.post(
            "/interface/list",
            json={"project_id": project_id, "q": keyword},
        )
        self._check_response(response)

        data = response.json()
        interfaces = data.get("data", {}).get("list", [])

        # Limit to 50 results as per specification
        return [YApiInterfaceSummary(**iface) for iface in interfaces[:50]]

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
        title: str,
        path: str,
        method: str,
        req_body: str = "",
        res_body: str = "",
        desc: str = "",
    ) -> int:
        """Create a new interface in YApi project.

        Args:
            project_id: Project ID
            title: Interface title
            path: Interface path (must start with /)
            method: HTTP method (GET, POST, etc.)
            req_body: Request body definition (JSON string, optional)
            res_body: Response body definition (JSON string, optional)
            desc: Interface description (optional)

        Returns:
            Created interface ID

        Raises:
            httpx.HTTPStatusError: For validation, permission, or server errors
        """
        payload: dict[str, Any] = {
            "project_id": project_id,
            "title": title,
            "path": path,
            "method": method.upper(),
        }

        if req_body:
            payload["req_body_other"] = req_body
        if res_body:
            payload["res_body"] = res_body
        if desc:
            payload["desc"] = desc

        response = await self.client.post("/interface/add", json=payload)
        self._check_response(response)

        data = response.json()
        return int(data["data"]["_id"])

    async def update_interface(
        self,
        interface_id: int,
        title: str | None = None,
        path: str | None = None,
        method: str | None = None,
        req_body: str | None = None,
        res_body: str | None = None,
        desc: str | None = None,
    ) -> bool:
        """Update an existing interface (partial update).

        Args:
            interface_id: Interface ID to update
            title: New title (optional)
            path: New path (optional)
            method: New HTTP method (optional)
            req_body: New request body definition (optional)
            res_body: New response body definition (optional)
            desc: New description (optional)

        Returns:
            True if update succeeded

        Raises:
            httpx.HTTPStatusError: For validation, permission, not found, or server errors
        """
        # Start with interface ID
        payload: dict[str, Any] = {"id": interface_id}

        # Add only provided fields (partial update)
        if title is not None:
            payload["title"] = title
        if path is not None:
            payload["path"] = path
        if method is not None:
            payload["method"] = method.upper()
        if req_body is not None:
            payload["req_body_other"] = req_body
        if res_body is not None:
            payload["res_body"] = res_body
        if desc is not None:
            payload["desc"] = desc

        response = await self.client.post("/interface/up", json=payload)
        self._check_response(response)

        return True
