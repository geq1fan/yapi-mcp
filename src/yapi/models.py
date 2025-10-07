"""Pydantic models for YApi API data structures."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class YApiInterface(BaseModel):
    """YApi interface complete definition from API responses."""

    model_config = ConfigDict(populate_by_name=True)

    id: int = Field(..., alias="_id", description="Interface ID")
    title: str = Field(..., description="Interface title")
    path: str = Field(..., description="Interface path", examples=["/api/user/login"])

    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"] = Field(
        ...,
        description="HTTP method",
    )

    project_id: int = Field(..., description="Project ID this interface belongs to")

    desc: str | None = Field(None, description="Interface description")
    req_body_other: str | None = Field(
        None, description="Request parameters definition (JSON string)"
    )
    res_body: str | None = Field(None, description="Response structure definition (JSON string)")
    status: str | None = Field(None, description="Status code")

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


class YApiProject(BaseModel):
    """YApi project information (optional, for future use)."""

    model_config = ConfigDict(populate_by_name=True)

    id: int = Field(..., alias="_id", description="Project ID")
    name: str = Field(..., description="Project name")
    desc: str | None = Field(None, description="Project description")
