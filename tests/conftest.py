"""Shared test utilities and fixtures."""


def make_cookies(token: str) -> dict[str, str]:
    return {"_yapi_token": token, "_yapi_uid": "uid", "ZYBIPSCAS": "cas"}
