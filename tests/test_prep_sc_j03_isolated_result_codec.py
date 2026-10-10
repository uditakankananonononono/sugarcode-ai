"""AUTHORED, NOT RUN. Pytest-style tests for self_improve.isolated_result_codec.
Interface unconfirmed against real isolated_dispatch.py."""
import json
import pytest
from sugarcode.self_improve.isolated_result_codec import (
    decode_child_result, ResultProtocolError, DEFAULT_MAX_BYTES)


def reason(raw, **kw):
    with pytest.raises(ResultProtocolError) as e:
        decode_child_result(raw, **kw)
    return e.value.reason


def test_valid_finite_result():
    assert decode_child_result(b'{"result": {"a": [1, 2.5, "x", null, true]}}\n') == {"a": [1, 2.5, "x", None, True]}

def test_valid_scalar_result():
    assert decode_child_result(b'{"result": 3}') == 3

def test_valid_null_result():
    assert decode_child_result(b'{"result": null}') is None

def test_unicode_result_ok():
    assert decode_child_result('{"result": "caf\u00e9 \u2603"}'.encode()) == "caf\u00e9 \u2603"

def test_bytearray_accepted():
    assert decode_child_result(bytearray(b'{"result": 1}')) == 1

def test_duplicate_top_level_result_key():
    assert reason(b'{"result": 1, "result": 2}') == "duplicate_key"

def test_duplicate_nested_key():
    assert reason(b'{"result": {"a": 1, "a": 2}}') == "duplicate_key"

def test_duplicate_key_in_list_object():
    assert reason(b'{"result": [{"k": 1, "k": 1}]}') == "duplicate_key"

def test_duplicate_key_via_escape_equivalence():
    assert reason(b'{"result": {"a": 1, "\\u0061": 2}}') == "duplicate_key"

@pytest.mark.parametrize("c", [b"NaN", b"Infinity", b"-Infinity"])
def test_nonfinite_constants_top_and_nested(c):
    assert reason(b'{"result": ' + c + b'}') == "nonfinite_constant"
    assert reason(b'{"result": {"x": [' + c + b']}}') == "nonfinite_constant"

def test_float_overflow_literal():
    assert reason(b'{"result": 1e999}') == "float_overflow"
    assert reason(b'{"result": {"x": -1e999}}') == "float_overflow"

def test_int_overflow_digits():
    assert reason(b'{"result": ' + b"9" * 65 + b'}', max_int_digits=64) == "int_overflow"

def test_int_at_digit_limit_ok():
    assert decode_child_result(b'{"result": ' + b"9" * 64 + b'}') == int("9" * 64)

def test_int_digit_limit_configurable():
    assert reason(b'{"result": 12345}', max_int_digits=4) == "int_overflow"

def test_extra_top_level_key():
    assert reason(b'{"result": 1, "extra": 2}') == "top_level_keys"

def test_missing_result_key():
    assert reason(b'{}') == "top_level_keys"
    assert reason(b'{"Result": 1}') == "top_level_keys"

@pytest.mark.parametrize("raw", [b'[1]', b'"x"', b'1', b'null', b'true'])
def test_top_level_not_object(raw):
    assert reason(raw) == "top_level_not_object"

def test_trailing_garbage():
    assert reason(b'{"result": 1} x') == "malformed_json"

def test_two_documents():
    assert reason(b'{"result": 1}\n{"result": 2}') == "malformed_json"

def test_empty_and_whitespace():
    assert reason(b'') == "empty"
    assert reason(b'   \n') == "malformed_json"

def test_truncated_json():
    assert reason(b'{"result": [1, 2') == "malformed_json"

def test_invalid_utf8():
    assert reason(b'{"result": "\xff"}') == "invalid_utf8"

def test_utf8_bom_rejected():
    assert reason(b'\xef\xbb\xbf{"result": 1}') == "malformed_json"

def test_lone_surrogate_value_and_key():
    assert reason(b'{"result": "\\ud800"}') == "invalid_unicode"
    assert reason(b'{"result": {"\\udc00": 1}}') == "invalid_unicode"

def test_not_bytes_types():
    assert reason('{"result": 1}') == "not_bytes"
    assert reason(None) == "not_bytes"
    assert reason(memoryview(b'{"result": 1}')) == "not_bytes"

def test_size_cap_exact_boundary():
    pad = DEFAULT_MAX_BYTES - len(b'{"result": ""}')
    ok = b'{"result": "' + b"a" * (pad) + b'"}'
    assert len(ok) == DEFAULT_MAX_BYTES
    assert len(decode_child_result(ok)) == pad

def test_size_cap_one_over():
    over = b'{"result": "' + b"a" * (DEFAULT_MAX_BYTES) + b'"}'
    assert reason(over) == "too_large"

def test_size_checked_before_decode():
    assert reason(b"\xff" * 20, max_bytes=10) == "too_large"

def test_depth_limit():
    deep = b'{"result": ' + b"[" * 70 + b"]" * 70 + b'}'
    assert reason(deep) == "too_deep"

def test_depth_pathological_recursion_is_protocol_error():
    deep = b'{"result": ' + b"[" * 200000 + b"]" * 200000 + b'}'
    assert reason(deep, max_bytes=10_000_000) == "too_deep"

def test_depth_at_limit_ok():
    raw = b'{"result": ' + b"[" * 60 + b"]" * 60 + b'}'
    assert decode_child_result(raw) is not None

def test_no_other_exception_type_for_random_garbage():
    for raw in (b"\x00", b"{", b'{"result":', b'{"result": 01}', b'{"result": +1}', b'{"result": .5}'):
        with pytest.raises(ResultProtocolError):
            decode_child_result(raw)

def test_roundtrip_of_json_dumps_allow_nan_false():
    payload = {"result": {"n": [0, -1, 1.5, "s", None], "b": False}}
    assert decode_child_result(json.dumps(payload, allow_nan=False).encode()) == payload["result"]

def test_error_is_valueerror_subclass():
    assert issubclass(ResultProtocolError, ValueError)
