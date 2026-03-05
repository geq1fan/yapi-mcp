"""Pydantic models for YApi API data structures."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class YApiInterface(BaseModel):
    """YApi interface complete definition from API responses."""

    model_config = ConfigDict(populate_by_name=True)

    id: int = Field(..., alias="_id", description="Interface ID")
    catid: int = Field(..., description="Category ID this interface belongs to")
    title: str = Field(..., description="Interface title")
    path: str = Field(..., description="Interface path", examples=["/api/user/login"])

    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"] = Field(
        ...,
        description="HTTP method",
    )

    project_id: int = Field(..., description="Project ID this interface belongs to")

    desc: str | None = Field(None, description="Interface description (HTML)")
    markdown: str | None = Field(None, description="Interface description (Markdown)")
    req_body_other: str | None = Field(
        None, description="Request body definition (JSON string)"
    )
    req_body_type: str | None = Field(None, description="Request body type (form/json/raw/file)")
    req_body_is_json_schema: bool | None = Field(
        None, description="Whether req_body is JSON Schema"
    )
    req_body_form: list[dict[str, Any]] | None = Field(
        None, description="Form body fields [{name, type, required, desc, example}]"
    )
    req_query: list[dict[str, Any]] | None = Field(
        None, description="Query parameters [{name, required, desc, example}]"
    )
    req_headers: list[dict[str, Any]] | None = Field(
        None, description="Request headers [{name, value, required, desc}]"
    )
    req_params: list[dict[str, Any]] | None = Field(
        None, description="Path parameters [{name, example, desc}]"
    )
    res_body: str | None = Field(None, description="Response body definition (JSON string)")
    res_body_type: str | None = Field(None, description="Response body type (json/raw)")
    res_body_is_json_schema: bool | None = Field(
        None, description="Whether res_body is JSON Schema"
    )
    status: str | None = Field(None, description="Interface status (undone/done)")
    tag: list[str] | None = Field(None, description="Interface tags")
    api_opened: bool | None = Field(None, description="Whether API is publicly accessible")

    add_time: int | None = Field(None, description="Creation timestamp (Unix epoch)")
    up_time: int | None = Field(None, description="Last update timestamp (Unix epoch)")


class YApiInterfaceSummary(BaseModel):
    """YApi interface summary from search results."""

    model_config = ConfigDict(populate_by_name=True)

    id: int = Field(..., alias="_id", description="Interface ID")
    title: str = Field(..., description="Interface title")
    path: str = Field(..., description="Interface path")
    method: str = Field(..., description="HTTP method")


class YApiErrorResponse(BaseModel):
    """YApi API error response structure."""

    errcode: int = Field(..., description="Error code (non-zero indicates error)")
    errmsg: str = Field(..., description="Error message")
