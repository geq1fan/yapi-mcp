"""Configuration management for YApi MCP Server."""

import os
from pathlib import Path

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE_ENV_VAR = "YAPI_ENV_FILE"


class EnvFileConfigurationError(ValueError):
    """Raised when the configured .env file path is invalid."""

    def __init__(self, env_path: Path) -> None:
        super().__init__(f"{ENV_FILE_ENV_VAR} must point to an existing .env file: {env_path}")


class ServerConfig(BaseSettings):
    """YApi MCP Server configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
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


def resolve_env_file_path() -> Path | None:
    """Resolve an explicit .env file path from the environment."""
    raw_env_file = os.getenv(ENV_FILE_ENV_VAR)
    if raw_env_file is None:
        return None

    env_file = raw_env_file.strip()
    if not env_file:
        return None

    env_path = Path(env_file).expanduser()
    if not env_path.is_file():
        raise EnvFileConfigurationError(env_path)

    return env_path


def load_server_config() -> ServerConfig:
    """Load server config from process env and optional explicit .env file."""
    env_file = resolve_env_file_path()
    return ServerConfig(_env_file=env_file)
