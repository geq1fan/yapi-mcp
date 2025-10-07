"""Unit tests for ServerConfig validation."""

import pytest
from pydantic import ValidationError

from src.config import ServerConfig


def test_server_config_valid():
    """Test ServerConfig with valid inputs."""
    config = ServerConfig(
        yapi_server_url="https://yapi.example.com",
        yapi_token="dummy-token",
        yapi_uid="dummy-uid",
        yapi_cas="dummy-cas",
    )

    assert str(config.yapi_server_url) == "https://yapi.example.com/"
    assert config.yapi_token == "dummy-token"
    assert config.yapi_uid == "dummy-uid"
    assert config.yapi_cas == "dummy-cas"


def test_server_config_cookies_property():
    """Test cookies property returns correct dictionary."""
    config = ServerConfig(
        yapi_server_url="https://yapi.example.com",
        yapi_token="dummy-token",
        yapi_uid="dummy-uid",
        yapi_cas="dummy-cas",
    )

    cookies = config.cookies
    assert cookies == {
        "_yapi_token": "dummy-token",
        "_yapi_uid": "dummy-uid",
        "ZYBIPSCAS": "dummy-cas",
    }


def test_server_config_missing_required_field():
    """Test ServerConfig raises ValidationError when required field is missing."""
    with pytest.raises(ValidationError) as exc_info:
        ServerConfig(
            yapi_server_url="https://yapi.example.com",
            yapi_uid="uid",
            # Missing yapi_token (required)
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("yapi_token",) for error in errors)


def test_server_config_empty_token():
    """Test ServerConfig rejects empty token string."""
    with pytest.raises(ValidationError) as exc_info:
        ServerConfig(
            yapi_server_url="https://yapi.example.com",
            yapi_token="",  # Empty string violates min_length=1
            yapi_uid="uid",
        )

    errors = exc_info.value.errors()
    assert any(
        error["loc"] == ("yapi_token",) and "at least 1 character" in error["msg"]
        for error in errors
    )


def test_server_config_invalid_url():
    """Test ServerConfig rejects invalid URL format."""
    with pytest.raises(ValidationError) as exc_info:
        ServerConfig(
            yapi_server_url="not-a-valid-url",
            yapi_token="dummy-token",
            yapi_uid="dummy-uid",
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("yapi_server_url",) for error in errors)


def test_server_config_http_url_allowed():
    """Test ServerConfig accepts HTTP URLs (not just HTTPS)."""
    config = ServerConfig(
        yapi_server_url="http://localhost:3000",
        yapi_token="dummy-token",
        yapi_uid="dummy-uid",
        yapi_cas="dummy-cas",
    )

    assert str(config.yapi_server_url) == "http://localhost:3000/"


def test_server_config_yapi_cas_optional():
    """Test yapi_cas is optional and defaults to None."""
    config = ServerConfig(
        yapi_server_url="https://yapi.example.com",
        yapi_token="dummy-token",
        yapi_uid="dummy-uid",
        # yapi_cas not provided
    )

    assert config.yapi_cas is None
    assert config.yapi_token == "dummy-token"
    assert config.yapi_uid == "dummy-uid"


def test_server_config_cookies_without_cas():
    """Test cookies property excludes ZYBIPSCAS when yapi_cas is not provided."""
    config = ServerConfig(
        yapi_server_url="https://yapi.example.com",
        yapi_token="dummy-token",
        yapi_uid="dummy-uid",
        # yapi_cas not provided
    )

    cookies = config.cookies
    assert cookies == {
        "_yapi_token": "dummy-token",
        "_yapi_uid": "dummy-uid",
    }
    assert "ZYBIPSCAS" not in cookies
