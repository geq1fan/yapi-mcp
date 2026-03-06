"""Unit tests for ServerConfig validation."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from yapi_mcp.config import ServerConfig


@pytest.fixture(autouse=True)
def clear_yapi_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent local shell or CI environment from affecting config tests."""
    for key in ("YAPI_SERVER_URL", "YAPI_TOKEN", "YAPI_UID", "YAPI_CAS"):
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


def test_server_config_ignores_unrelated_dotenv_keys(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test unrelated keys in the current working directory .env file are ignored."""
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "\n".join(
            [
                "YAPI_SERVER_URL=https://yapi.example.com",
                "YAPI_TOKEN=dummy-token",
                "YAPI_UID=dummy-uid",
                "PYPI_TOKEN=ignored-value",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("YAPI_SERVER_URL", raising=False)
    monkeypatch.delenv("YAPI_TOKEN", raising=False)
    monkeypatch.delenv("YAPI_UID", raising=False)
    monkeypatch.delenv("YAPI_CAS", raising=False)

    config = ServerConfig()

    assert str(config.yapi_server_url) == "https://yapi.example.com/"
    assert config.yapi_token == "dummy-token"  # noqa: S105
    assert config.yapi_uid == "dummy-uid"
    assert config.yapi_cas is None
