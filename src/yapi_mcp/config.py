"""Configuration management for YApi MCP Server."""

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseSettings):
    """YApi MCP Server configuration loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    yapi_server_url: HttpUrl = Field(
        ...,
        description="YApi server base URL",
        examples=["https://yapi.example.com"],
    )

    yapi_token: str = Field(
        ...,
        min_length=1,
        description="YApi authentication token (_yapi_token cookie)",
    )

    yapi_uid: str = Field(
        ...,
        min_length=1,
        description="YApi user ID (_yapi_uid cookie)",
    )

    yapi_cas: str | None = Field(
        default=None,
        description="Optional CAS authentication cookie (e.g., ZYBIPSCAS for custom deployments)",
    )

    @property
    def cookies(self) -> dict[str, str]:
        """Return cookies dictionary for YApi API authentication."""
        cookies = {
            "_yapi_token": self.yapi_token,
            "_yapi_uid": self.yapi_uid,
        }
        if self.yapi_cas:
            cookies["ZYBIPSCAS"] = self.yapi_cas
        return cookies
