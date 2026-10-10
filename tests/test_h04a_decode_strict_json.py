"""AUTHORED, NOT RUN. H04a: decode_strict_json (new entry) and decode_tool_arguments as its thin caller.
Written before the code change. Existing tests/test_prep_g02_tool_call_codec.py is untouched and is the
pin for the unchanged dict behavior."""
import pytest

from sugarcode.llm.tool_call_codec import (
    DEFAULT_MAX_CHARS, DEFAULT_MAX_DEPTH, ToolCallDecodeError, decode_strict_json, decode_tool_arguments)

CAP = 10_000


def reason(text, **kw):
    kw.setdefault("max_chars", CAP)
    with pytest.raises(ToolCallDecodeError) as e:
        decode_strict_json(text, **kw)
    return e.value.reason


def test_exported_and_defaults_unchanged():
    from sugarcode.llm import tool_call_codec as C
    assert "decode_strict_json" in C.__all__
    assert DEFAULT_MAX_CHARS == 65_536 and DEFAULT_MAX_DEPTH == 64


def test_list_root_valid_for_array_and_any():
    text = '[{"name": "a", "n": 1.5}, {"name": "b"}]'
    want = [{"name": "a", "n": 1.5}, {"name": "b"}]
    assert decode_strict_json(text, CAP, root="array") == want
    assert decode_strict_json(text, CAP) == want
    assert decode_strict_json(text, CAP, root="any") == want


def test_dict_root_valid_for_object_and_any():
    assert decode_strict_json('{"a": 1}', CAP, root="object") == {"a": 1}
    assert decode_strict_json('{"a": 1}', CAP) == {"a": 1}


def test_scalar_roots_only_with_any():
    assert decode_strict_json("3", CAP, root="any") == 3
    assert decode_strict_json("null", CAP, root="any") is None
    assert reason("3", root="array") == "not_array"
    assert reason("3", root="object") == "not_object"


def test_wrong_root_kind_typed():
    assert reason('{"a": 1}', root="array") == "not_array"
    assert reason("[1]", root="object") == "not_object"
    assert reason('"x"', root="array") == "not_array"


@pytest.mark.parametrize("root", ["array", "object", "any"])
@pytest.mark.parametrize("blank", ["", " ", "\t\r\n ", "  \n"])
def test_blank_text_is_invalid_json_not_empty_object(root, blank):
    assert reason(blank, root=root) == "invalid_json"


def test_blank_over_cap_reports_too_large_first():
    assert reason(" " * 11, max_chars=10) == "too_large"


@pytest.mark.parametrize("text", ['[{"a": 1, "a": 2}]', '[[{"k": 1, "k": 1}]]', '{"a": 1, "\\u0061": 2}'])
def test_duplicate_keys_rejected_at_any_depth(text):
    assert reason(text) == "duplicate_key"


@pytest.mark.parametrize("text", ["[NaN]", "[Infinity]", "[-Infinity]", "[1e999]", '[{"a": -1e999}]', "NaN"])
def test_non_finite_rejected(text):
    assert reason(text) == "non_finite"


@pytest.mark.parametrize("text", ["[1,]", "[", "[1] x", "[1][2]", "{'a': 1}", "\x00", "\u00a0[1]"])
def test_malformed_json(text):
    assert reason(text) == "invalid_json"


@pytest.mark.parametrize("bad", [None, 1, 1.5, True, b"[]", bytearray(b"[]"), ["a"], {"a": 1}])
def test_non_text_is_not_text_even_for_a_dict(bad):
    assert reason(bad) == "not_text"


def test_size_cap_in_characters_and_before_parse():
    ok = '["' + "x" * 20 + '"]'
    assert decode_strict_json(ok, len(ok), root="array") == ["x" * 20]
    assert reason(ok, max_chars=len(ok) - 1) == "too_large"
    assert reason("[" * (CAP + 1)) == "too_large"


def _nest(n):  # list root is depth 1
    return "[" * n + "]" * n


def test_depth_exactly_at_cap_ok_and_one_over_rejected():
    assert decode_strict_json(_nest(64), CAP, root="array") is not None
    assert reason(_nest(65), root="array") == "too_deep"


def test_custom_max_depth_and_extreme_nesting_typed():
    assert decode_strict_json(_nest(3), CAP, max_depth=3) is not None
    assert reason(_nest(4), max_depth=3) == "too_deep"
    assert reason("[" * 200_000 + "]" * 200_000, max_chars=1_000_000) == "too_deep"


def test_text_exactly_at_char_cap_with_many_items_ok():
    # 30 items: text length 61. Every value is at least one character, so for text the node count
    # cannot exceed max_chars; the node cap is a defensive bound shared with the direct-dict walk.
    text = "[" + ",".join(["1"] * 30) + "]"
    assert len(text) == 61
    assert len(decode_strict_json(text, 61)) == 30


@pytest.mark.parametrize("bad", [True, 1.5, "10", None])
def test_cap_types_are_plain_type_errors(bad):
    with pytest.raises(TypeError) as e:
        decode_strict_json("[]", bad)
    assert not isinstance(e.value, ToolCallDecodeError)
    with pytest.raises(TypeError):
        decode_strict_json("[]", CAP, max_depth=bad)


@pytest.mark.parametrize("bad", [0, -1])
def test_max_chars_range(bad):
    with pytest.raises(ValueError) as e:
        decode_strict_json("[]", bad)
    assert not isinstance(e.value, ToolCallDecodeError)


@pytest.mark.parametrize("bad", [0, -1, 65])
def test_max_depth_range(bad):
    with pytest.raises(ValueError):
        decode_strict_json("[]", CAP, max_depth=bad)


@pytest.mark.parametrize("bad", ["list", "dict", "", None, "ARRAY", ["array"], ("array",), 1, True, b"array", {"array"}])
def test_bad_root_value_is_plain_value_error(bad):
    with pytest.raises(ValueError) as e:
        decode_strict_json("[]", CAP, root=bad)
    assert type(e.value) is ValueError


def test_max_chars_required():
    with pytest.raises(TypeError):
        decode_strict_json("[]")


def test_error_is_value_error_with_reason():
    with pytest.raises(ValueError):
        decode_strict_json("[", CAP)


# ---- decode_tool_arguments unchanged through the thin-caller refactor ----
def test_tool_arguments_blank_still_empty_dict():
    for b in ("", "  ", " \t\r\n "):
        assert decode_tool_arguments(b, CAP) == {}


def test_tool_arguments_array_still_not_object():
    for t in ("[]", "[1]", "3", '"x"', "null", "true"):
        with pytest.raises(ToolCallDecodeError) as e:
            decode_tool_arguments(t, CAP)
        assert e.value.reason == "not_object"


def test_tool_arguments_direct_dict_same_object_and_not_text_for_others():
    d = {"a": [1, {"b": None}]}
    assert decode_tool_arguments(d, CAP) is d
    for bad in (None, 1, b"{}", ["a"], ("a",)):
        with pytest.raises(ToolCallDecodeError) as e:
            decode_tool_arguments(bad, CAP)
        assert e.value.reason == "not_text"


def test_tool_arguments_reasons_match_strict_for_objects():
    for text, want in (('{"a": 1, "a": 2}', "duplicate_key"), ('{"a": NaN}', "non_finite"),
                       ("{", "invalid_json"), ("x" * (CAP + 1), "too_large")):
        with pytest.raises(ToolCallDecodeError) as e:
            decode_tool_arguments(text, CAP)
        assert e.value.reason == want
        with pytest.raises(ToolCallDecodeError) as e2:
            decode_strict_json(text, CAP, root="object")
        assert e2.value.reason == want


# ---- size check runs BEFORE the blank check (original G02 order, preserved) ----
@pytest.mark.parametrize("blank", [" " * 11, "\t" * 11, " \r\n" * 4])
def test_oversized_blank_is_too_large_for_tool_arguments(blank):
    assert len(blank) > 10
    with pytest.raises(ToolCallDecodeError) as e:
        decode_tool_arguments(blank, 10)
    assert e.value.reason == "too_large"


@pytest.mark.parametrize("root", ["object", "array", "any"])
def test_oversized_blank_is_too_large_for_strict_entry(root):
    assert reason(" " * 11, max_chars=10, root=root) == "too_large"


def test_blank_at_cap_still_empty_dict_for_tool_arguments_only():
    assert decode_tool_arguments(" " * 10, 10) == {}
    assert reason(" " * 10, max_chars=10) == "invalid_json"
