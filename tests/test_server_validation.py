"""Unit tests for _validate_interface_request in server.py."""

import pytest

from yapi_mcp.server import _validate_interface_request


# --- 枚举值验证 ---

def test_invalid_method_raises():
    with pytest.raises(ValueError, match="method"):
        _validate_interface_request(method="INVALID")


def test_valid_methods_pass():
    for method in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:
        _validate_interface_request(method=method)  # 不应抛出


def test_invalid_req_body_type_raises():
    with pytest.raises(ValueError, match="req_body_type"):
        _validate_interface_request(req_body_type="xml")


def test_valid_req_body_types_pass():
    for t in ["form", "json", "raw", "file"]:
        _validate_interface_request(req_body_type=t)


def test_invalid_res_body_type_raises():
    with pytest.raises(ValueError, match="res_body_type"):
        _validate_interface_request(res_body_type="xml")


def test_valid_res_body_types_pass():
    for t in ["json", "raw"]:
        _validate_interface_request(res_body_type=t)


def test_invalid_status_raises():
    with pytest.raises(ValueError, match="status"):
        _validate_interface_request(status="invalid")


def test_valid_statuses_pass():
    for s in ["undone", "done"]:
        _validate_interface_request(status=s)


# --- 互斥校验 ---

def test_req_body_and_req_body_form_mutually_exclusive():
    with pytest.raises(ValueError, match="不能同时提供"):
        _validate_interface_request(
            req_body='{"type":"object"}',
            req_body_form='[{"name":"field1"}]',
        )


# --- body type 相关性验证 ---

def test_form_type_with_req_body_raises():
    with pytest.raises(ValueError, match="form"):
        _validate_interface_request(
            req_body_type="form",
            req_body='{"type":"object"}',
        )


def test_json_type_with_req_body_form_raises():
    with pytest.raises(ValueError, match="json"):
        _validate_interface_request(
            req_body_type="json",
            req_body_form='[{"name":"field1"}]',
        )


def test_raw_type_with_req_body_form_raises():
    with pytest.raises(ValueError, match="raw"):
        _validate_interface_request(
            req_body_type="raw",
            req_body_form='[{"name":"field1"}]',
        )


def test_file_type_with_req_body_raises():
    with pytest.raises(ValueError, match="file"):
        _validate_interface_request(
            req_body_type="file",
            req_body='{"type":"object"}',
        )


def test_file_type_with_req_body_form_raises():
    with pytest.raises(ValueError, match="file"):
        _validate_interface_request(
            req_body_type="file",
            req_body_form='[{"name":"field1"}]',
        )


# --- JSON 数组格式验证 ---

def test_invalid_json_in_req_query_raises():
    with pytest.raises(ValueError, match="req_query"):
        _validate_interface_request(req_query="not json")


def test_non_array_json_in_req_query_raises():
    with pytest.raises(ValueError, match="req_query"):
        _validate_interface_request(req_query='{"key": "value"}')


def test_invalid_json_in_req_headers_raises():
    with pytest.raises(ValueError, match="req_headers"):
        _validate_interface_request(req_headers="not json")


def test_invalid_json_in_req_params_raises():
    with pytest.raises(ValueError, match="req_params"):
        _validate_interface_request(req_params="not json")


def test_invalid_json_in_tag_raises():
    with pytest.raises(ValueError, match="tag"):
        _validate_interface_request(tag="not json")


def test_valid_json_array_in_req_query_passes():
    _validate_interface_request(req_query='[{"name":"page","required":"0"}]')


def test_valid_json_array_in_tag_passes():
    _validate_interface_request(tag='["tag1","tag2"]')


# --- 所有参数为 None/空时不报错 ---

def test_all_none_passes():
    _validate_interface_request()  # 所有参数都有默认值 None，不应抛出


def test_empty_strings_pass():
    _validate_interface_request(
        req_body="",
        req_body_form="",
        req_query="",
        req_headers="",
        req_params="",
        tag="",
    )
