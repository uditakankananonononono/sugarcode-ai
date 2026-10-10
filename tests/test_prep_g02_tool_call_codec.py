"""AUTHORED, NOT RUN. Tests for sugarcode.llm.tool_call_codec (G02 prep), written before the module.
Import path unverified against the pyproject layout."""
import sys

import pytest

from sugarcode.llm.tool_call_codec import (
    DEFAULT_MAX_CHARS, DEFAULT_MAX_DEPTH, ToolCallDecodeError, decode_tool_arguments, guarded_call)

CAP = 10_000


def reason(text, **kw):
    kw.setdefault("max_chars", CAP)
    with pytest.raises(ToolCallDecodeError) as e:
        decode_tool_arguments(text, **kw)
    return e.value.reason


def test_defaults_are_documented_values():
    assert DEFAULT_MAX_DEPTH == 64
    assert type(DEFAULT_MAX_CHARS) is int and DEFAULT_MAX_CHARS > 0


def test_valid_object():
    assert decode_tool_arguments('{"a": [1, 2.5, "x", null, true], "b": {"c": 1}}', CAP) == {
        "a": [1, 2.5, "x", None, True], "b": {"c": 1}}


def test_empty_object_and_empty_or_whitespace_text():
    assert decode_tool_arguments("{}", CAP) == {}
    assert decode_tool_arguments("", CAP) == {}
    assert decode_tool_arguments("  ", CAP) == {}
    assert decode_tool_arguments(" \t\r\n ", CAP) == {}


def test_unicode_keys_and_values_ok():
    assert decode_tool_arguments('{"módulo": "中文"}', CAP) == {"módulo": "中文"}


def test_error_is_value_error_subclass_with_reason():
    with pytest.raises(ValueError):
        decode_tool_arguments("{", CAP)
    assert reason("{") == "invalid_json"


@pytest.mark.parametrize("text", ['{"a": 1, "a": 2}', '{"a": {"b": 1, "b": 1}}', '{"a": [{"k": 1, "k": 1}]}',
                                  '{"a": 1, "\\u0061": 2}'])
def test_duplicate_keys_rejected_at_any_depth(text):
    assert reason(text) == "duplicate_key"


@pytest.mark.parametrize("text", ['{"a": NaN}', '{"a": Infinity}', '{"a": -Infinity}', '{"a": [NaN]}',
                                  '{"a": 1e999}', '{"a": -1e999}', '{"a": 1E400}'])
def test_non_finite_rejected_not_coerced(text):
    assert reason(text) == "non_finite"


@pytest.mark.parametrize("text", ["[]", "[1]", "3", '"x"', "null", "true"])
def test_top_level_must_be_object(text):
    assert reason(text) == "not_object"


@pytest.mark.parametrize("text", ["{'a': 1}", '{"a": 1,}', '{"a": }', "{", '{"a": 1} x', '{"a": 1}{"b": 2}',
                                  "\x00", '{"a": "\\ud83d"', "\u00a0"])
def test_malformed_json(text):
    assert reason(text) == "invalid_json"


@pytest.mark.parametrize("bad", [None, 1, 1.5, True, b"{}", bytearray(b"{}"), ["a"], ("a",), {"a"}])
def test_non_text_rejected(bad):
    assert reason(bad) == "not_text"


def test_size_cap_checked_in_characters():
    ok = '{"a": "' + "x" * 20 + '"}'
    assert decode_tool_arguments(ok, len(ok)) == {"a": "x" * 20}
    assert reason(ok, max_chars=len(ok) - 1) == "too_large"
    uni = '{"a": "' + "中" * 10 + '"}'
    assert decode_tool_arguments(uni, len(uni)) == {"a": "中" * 10}
    assert reason(uni, max_chars=len(uni) - 1) == "too_large"


def test_size_cap_applies_before_parse():
    assert reason("{" * (CAP + 1)) == "too_large"


def _nest(n):
    return '{"a": ' + "[" * (n - 1) + "]" * (n - 1) + "}"  # object is depth 1, lists add n-1


def test_depth_exactly_at_cap_ok_and_one_over_rejected():
    assert decode_tool_arguments(_nest(64), CAP) is not None
    assert reason(_nest(65)) == "too_deep"


def test_custom_max_depth():
    assert decode_tool_arguments(_nest(3), CAP, max_depth=3) is not None
    assert reason(_nest(4), max_depth=3) == "too_deep"


def test_extreme_nesting_is_typed_not_recursion_error():
    r = reason('{"a": ' + "[" * 200_000 + "]" * 200_000 + "}", max_chars=1_000_000)
    assert r in ("too_deep",)


def test_wide_object_not_depth_limited():
    text = "{" + ",".join('"k%d": 1' % i for i in range(1000)) + "}"
    assert len(decode_tool_arguments(text, 100_000)) == 1000


@pytest.mark.skipif(not hasattr(sys, "set_int_max_str_digits"), reason="needs the int digit limit")
def test_huge_int_digit_limit_is_typed():
    old = sys.get_int_max_str_digits()
    sys.set_int_max_str_digits(640)
    try:
        assert reason('{"n": ' + "1" * 700 + "}") == "invalid_json"
    finally:
        sys.set_int_max_str_digits(old)


@pytest.mark.parametrize("bad", [True, 1.5, "10", None])
def test_max_chars_type_checked(bad):
    with pytest.raises(TypeError):
        decode_tool_arguments("{}", bad)


@pytest.mark.parametrize("bad", [0, -1])
def test_max_chars_range_checked(bad):
    with pytest.raises(ValueError):
        decode_tool_arguments("{}", bad)


@pytest.mark.parametrize("bad", [True, 1.5, "64", None])
def test_max_depth_type_checked(bad):
    with pytest.raises(TypeError):
        decode_tool_arguments("{}", CAP, max_depth=bad)


@pytest.mark.parametrize("bad", [0, -1, 65])
def test_max_depth_range_checked(bad):
    with pytest.raises(ValueError):
        decode_tool_arguments("{}", CAP, max_depth=bad)


def test_cap_misuse_is_not_a_decode_error():
    with pytest.raises(TypeError) as e:
        decode_tool_arguments("{}", True)
    assert not isinstance(e.value, ToolCallDecodeError)
    with pytest.raises(ValueError) as e2:
        decode_tool_arguments("{}", 0)
    assert not isinstance(e2.value, ToolCallDecodeError)


def test_max_chars_is_required():
    with pytest.raises(TypeError):
        decode_tool_arguments("{}")


# ---- guarded_call ----
def test_guarded_call_returns_result():
    assert guarded_call(lambda a, b=0: a + b, 1, b=2) == {"result": 3}


def test_guarded_call_result_none_is_still_result():
    assert guarded_call(lambda: None) == {"result": None}


def test_guarded_call_catches_exception_into_error():
    def boom():
        raise KeyError("k")
    assert guarded_call(boom) == {"error": "KeyError: 'k'"}


@pytest.mark.parametrize("exc", [ImportError("no mod"), AttributeError("no attr"), RecursionError("deep"),
                                 MemoryError("mem"), ZeroDivisionError("z")])
def test_guarded_call_catches_import_attr_recursion_memory(exc):
    def boom():
        raise exc
    out = guarded_call(boom)
    assert list(out) == ["error"] and out["error"].startswith(type(exc).__name__ + ": ")


def test_guarded_call_lookup_failure_inside_callable_is_caught():
    import importlib
    out = guarded_call(lambda: getattr(importlib.import_module("sugarcode.modules._no_such_mod_"), "f")())
    assert list(out) == ["error"]


def test_guarded_call_does_not_swallow_base_exceptions():
    def stop():
        raise KeyboardInterrupt
    with pytest.raises(KeyboardInterrupt):
        guarded_call(stop)
    def exit_():
        raise SystemExit(1)
    with pytest.raises(SystemExit):
        guarded_call(exit_)


def test_guarded_call_truncates_long_message():
    def boom():
        raise ValueError("x" * 5000)
    out = guarded_call(boom)
    assert len(out["error"]) <= 600


def test_guarded_call_survives_exception_whose_str_raises():
    class Bad(Exception):
        def __str__(self):
            raise RuntimeError("no str")
    out = guarded_call(lambda: (_ for _ in ()).throw(Bad()))
    assert list(out) == ["error"] and out["error"].startswith("Bad")


# ---- direct dict path: same walk, no unvalidated bypass ----
def _deep_dict(n):
    d = {}
    for _ in range(n - 1):
        d = {"a": d}
    return d  # depth n


def test_direct_dict_returned_same_object():
    d = {"a": [1, {"b": None}]}
    assert decode_tool_arguments(d, CAP) is d


def test_direct_dict_depth_cap_exact_and_over():
    assert decode_tool_arguments(_deep_dict(64), CAP) is not None
    assert reason(_deep_dict(65)) == "too_deep"
    assert reason(_deep_dict(4), max_depth=3) == "too_deep"


def test_direct_dict_list_and_tuple_count_as_depth():
    x = {"a": [[[[[]]]]]}  # dict=1 plus five nested lists = depth 6
    assert reason(x, max_depth=5) == "too_deep"
    y = {"a": ((((),),),)}
    assert reason(y, max_depth=4) == "too_deep"


def test_direct_dict_cycle_terminates_typed():
    d = {}
    d["self"] = d
    assert reason(d) == "too_deep"
    lst = []
    lst.append(lst)
    assert reason({"a": lst}) == "too_deep"


def test_direct_dict_shared_reference_blowup_is_capped():
    x = [None]
    for _ in range(40):
        x = [x, x]  # depth 41, 2**40 paths
    assert reason({"a": x}, max_chars=1000) == "too_large"


def test_direct_dict_node_cap_uses_max_chars():
    d = {"a": list(range(50))}
    assert decode_tool_arguments(d, 60) is d
    assert reason(d, max_chars=40) == "too_large"


def test_direct_dict_non_string_key_at_any_level():
    assert reason({1: "x"}) == "non_string_key"
    assert reason({"a": [{2: "x"}]}) == "non_string_key"


def test_direct_dict_caps_are_still_typed():
    with pytest.raises(TypeError):
        decode_tool_arguments({"a": 1}, True)
    with pytest.raises(ValueError):
        decode_tool_arguments({"a": 1}, CAP, max_depth=65)


def test_validate_then_execute_pattern_never_executes_on_failure():
    """Pattern the wiring uses: decode first, run only on success. (call_tool-level test is the UNAPPLIED proposal.)"""
    ran = []

    def run(args):
        try:
            a = decode_tool_arguments(args, CAP)
        except ToolCallDecodeError as e:
            return {"error": e.reason}
        return guarded_call(lambda: ran.append(a) or "done")

    bad = ['{"a": 1, "a": 2}', '{"a": NaN}', "[]", "x" * (CAP + 1), _deep_dict(65), {1: 2}, ["a"], None]
    for b in bad:
        assert "error" in run(b)
    assert ran == []
    assert run('{"a": 1}') == {"result": "done"} and ran == [{"a": 1}]
