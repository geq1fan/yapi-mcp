"""Tests for startup credential validation error reporting."""

from pathlib import Path

import httpx
import pytest

from yapi_mcp import server
from yapi_mcp.server import _print_startup_http_error

BASE_URL = "https://yapi.example.com"


def _make_http_status_error(status_code: int, payload: dict | None = None) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", f"{BASE_URL}/api/user/status")
    response = httpx.Response(status_code, request=request, json=payload)
    return httpx.HTTPStatusError("startup validation failed", request=request, response=response)


def test_print_startup_http_error_for_auth_failure(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test auth failures mention credential env vars instead of generic hints."""
    error = _make_http_status_error(401, {"errcode": 401, "errmsg": "未登录"})

    _print_startup_http_error(error, has_cas_cookie=False)

    captured = capsys.readouterr()
    assert "认证失败" in captured.err
    assert "YAPI_TOKEN, YAPI_UID, and optional YAPI_CAS" in captured.err


def test_print_startup_http_error_for_not_found(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test non-auth failures point to URL/CAS diagnosis instead of expired cookie."""
    error = _make_http_status_error(404, {"errcode": 404, "errmsg": "Not Found"})

    _print_startup_http_error(error, has_cas_cookie=False)

    captured = capsys.readouterr()
    assert "Startup validation request to /api/user/status failed" in captured.err
    assert "YAPI_SERVER_URL" in captured.err
    assert "YAPI_CAS" in captured.err
    assert "Cookie may be expired" not in captured.err


def test_main_exits_cleanly_on_startup_validation_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test startup validation failures exit with code 1 without extra traceback logging."""

    def raise_startup_error() -> None:
        exception_group_message = "startup"
        raise ExceptionGroup(exception_group_message, [server.MCPStartupError()])

    monkeypatch.setattr(server.mcp, "run", raise_startup_error)

    with pytest.raises(SystemExit, match="1"):
        server.main()

    captured = capsys.readouterr()
    assert captured.err == ""


@pytest.mark.asyncio
async def test_app_lifespan_reports_invalid_env_file(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test invalid YAPI_ENV_FILE paths get a dedicated startup error."""

    def raise_invalid_env_file() -> None:
        raise server.EnvFileConfigurationError(Path("missing.env"))

    monkeypatch.setattr(server, "get_config", raise_invalid_env_file)

    with pytest.raises(server.MCPStartupError):
        async with server.app_lifespan(server.mcp):
            pass

    captured = capsys.readouterr()
    assert "YAPI_ENV_FILE" in captured.err
    assert "disable .env loading" in captured.err
