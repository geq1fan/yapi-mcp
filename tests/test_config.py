"""Unit tests for ServerConfig validation."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from yapi_mcp.config import (
    ENV_FILE_ENV_VAR,
    EnvFileConfigurationError,
    ServerConfig,
    load_server_config,
    resolve_env_file_path,
)


@pytest.fixture(autouse=True)
def clear_yapi_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent local shell or CI environment from affecting config tests."""
    for key in ("YAPI_SERVER_URL", "YAPI_TOKEN", "YAPI_UID", "YAPI_CAS", ENV_FILE_ENV_VAR):
        monkeypatch.delenv(key, raising=False)


def test_server_config_valid() -> None:
    """Test ServerConfig with valid inputs."""
    config = ServerConfig(
        yapi_server_url="https://yapi.example.com",
        yapi_token="dummy-token",  # noqa: S106
        yapi_uid="dummy-uid",
        yapi_cas="dummy-cas",
        _env_file=None,
    )

    assert str(config.yapi_server_url) == "https://yapi.example.com/"
    assert config.yapi_token == "dummy-token"  # noqa: S105
    assert config.yapi_uid == "dummy-uid"
    assert config.yapi_cas == "dummy-cas"


def test_server_config_cookies_property() -> None:
    """Test cookies property returns correct dictionary."""
    config = ServerConfig(
        yapi_server_url="https://yapi.example.com",
        yapi_token="dummy-token",  # noqa: S106
        yapi_uid="dummy-uid",
        yapi_cas="dummy-cas",
        _env_file=None,
    )

    cookies = config.cookies
    assert cookies == {
        "_yapi_token": "dummy-token",
        "_yapi_uid": "dummy-uid",
        "ZYBIPSCAS": "dummy-cas",
    }


def test_server_config_missing_required_field() -> None:
    """Test ServerConfig raises ValidationError when required field is missing."""
    with pytest.raises(ValidationError) as exc_info:
        ServerConfig(
            yapi_server_url="https://yapi.example.com",
            yapi_uid="uid",
            # Missing yapi_token (required)
            _env_file=None,
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("yapi_token",) for error in errors)


def test_server_config_empty_token() -> None:
    """Test ServerConfig rejects empty token string."""
    with pytest.raises(ValidationError) as exc_info:
        ServerConfig(
            yapi_server_url="https://yapi.example.com",
            yapi_token="",  # Empty string violates min_length=1
            yapi_uid="uid",
            _env_file=None,
        )

    errors = exc_info.value.errors()
    assert any(
        error["loc"] == ("yapi_token",) and "at least 1 character" in error["msg"]
        for error in errors
    )


def test_server_config_invalid_url() -> None:
    """Test ServerConfig rejects invalid URL format."""
    with pytest.raises(ValidationError) as exc_info:
        ServerConfig(
            yapi_server_url="not-a-valid-url",
            yapi_token="dummy-token",  # noqa: S106
            yapi_uid="dummy-uid",
            _env_file=None,
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("yapi_server_url",) for error in errors)


def test_server_config_http_url_allowed() -> None:
    """Test ServerConfig accepts HTTP URLs (not just HTTPS)."""
    config = ServerConfig(
        yapi_server_url="http://localhost:3000",
        yapi_token="dummy-token",  # noqa: S106
        yapi_uid="dummy-uid",
        yapi_cas="dummy-cas",
        _env_file=None,
    )

    assert str(config.yapi_server_url) == "http://localhost:3000/"


def test_server_config_yapi_cas_optional() -> None:
    """Test yapi_cas is optional and defaults to None."""
    config = ServerConfig(
        yapi_server_url="https://yapi.example.com",
        yapi_token="dummy-token",  # noqa: S106
        yapi_uid="dummy-uid",
        # yapi_cas not provided
        _env_file=None,
    )

    assert config.yapi_cas is None
    assert config.yapi_token == "dummy-token"  # noqa: S105
    assert config.yapi_uid == "dummy-uid"


def test_server_config_cookies_without_cas() -> None:
    """Test cookies property excludes ZYBIPSCAS when yapi_cas is not provided."""
    config = ServerConfig(
        yapi_server_url="https://yapi.example.com",
        yapi_token="dummy-token",  # noqa: S106
        yapi_uid="dummy-uid",
        # yapi_cas not provided
        _env_file=None,
    )

    cookies = config.cookies
    assert cookies == {
        "_yapi_token": "dummy-token",
        "_yapi_uid": "dummy-uid",
    }
    assert "ZYBIPSCAS" not in cookies


def test_server_config_does_not_read_cwd_dotenv_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test current working directory .env is not loaded implicitly."""
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        (
            "YAPI_SERVER_URL=https://yapi.example.com\n"
            "YAPI_TOKEN=dummy-token\n"
            "YAPI_UID=dummy-uid\n"
            "PYPI_TOKEN=ignored-value"
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValidationError) as exc_info:
        ServerConfig()

    missing_fields = {error["loc"][0] for error in exc_info.value.errors()}
    assert {"yapi_server_url", "yapi_token", "yapi_uid"}.issubset(missing_fields)


@pytest.mark.parametrize("env_file_value", ["", "   "])
def test_resolve_env_file_path_ignores_blank_values(
    env_file_value: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test blank YAPI_ENV_FILE values disable .env loading."""
    monkeypatch.setenv(ENV_FILE_ENV_VAR, env_file_value)

    assert resolve_env_file_path() is None


def test_resolve_env_file_path_raises_for_missing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test invalid YAPI_ENV_FILE paths fail with a clear error."""
    missing_path = tmp_path / "missing.env"
    monkeypatch.setenv(ENV_FILE_ENV_VAR, str(missing_path))

    with pytest.raises(EnvFileConfigurationError, match=str(missing_path)):
        resolve_env_file_path()


def test_load_server_config_from_explicit_env_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test explicit YAPI_ENV_FILE path is loaded, including relative paths."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    dotenv_path = config_dir / "yapi.env"
    dotenv_path.write_text(
        (
            "YAPI_SERVER_URL=https://yapi.example.com\n"
            "YAPI_TOKEN=dummy-token\n"
            "YAPI_UID=dummy-uid\n"
            "PYPI_TOKEN=ignored-value"
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(ENV_FILE_ENV_VAR, "config/yapi.env")

    config = load_server_config()

    assert str(config.yapi_server_url) == "https://yapi.example.com/"
    assert config.yapi_token == "dummy-token"  # noqa: S105
    assert config.yapi_uid == "dummy-uid"
    assert config.yapi_cas is None
