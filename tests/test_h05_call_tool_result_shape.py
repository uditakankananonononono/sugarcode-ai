"""AUTHORED, NOT RUN. H05: characterize call_tool result shaping (tools.py 184-188): the 12000-char
truncation and the non-finite float mapping. TEST ONLY, no source change.
Uses the same fake-catalog / fake-import pattern as tests/test_g03_call_tool_no_execution.py, so no real
module runs. Deliberately NOT asserted: set ordering, tuple-key collision, depth>8 fallback."""
import json
import types

import pytest

import sugarcode.llm.tools as T

LIMIT = 12000


@pytest.fixture
def returning(monkeypatch):
    """returning(value) makes tool m__f return `value`; call with T.call_tool("m__f", {"a": "x"})."""
    holder = {}
    tool = T.Tool(name="m__f", module="m", function="f", description="d",
                  parameters={"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]})
    monkeypatch.setattr(T, "catalog", lambda: {"m__f": tool})
    monkeypatch.setattr(T.importlib, "import_module",
                        lambda name: types.SimpleNamespace(f=lambda **kw: holder["value"]))

    def setup(value):
        holder["value"] = value
        return lambda: T.call_tool("m__f", {"a": "x"})
    return setup


def _padded(total_len):
    """A dict whose json.dumps text has exactly total_len characters (ASCII padding)."""
    base = len(json.dumps({"s": ""}))
    value = {"s": "x" * (total_len - base)}
    assert len(json.dumps(value)) == total_len
    return value


def test_exactly_12000_returns_result_not_truncated(returning):
    value = _padded(LIMIT)
    out = returning(value)()
    assert out == {"result": value}
    assert "result_truncated" not in out and "result_preview" not in out


def test_12001_chars_is_truncated_with_exact_shape(returning):
    value = _padded(LIMIT + 1)
    out = returning(value)()
    assert set(out) == {"result_truncated", "result_preview"}
    assert out["result_truncated"] is True
    assert "result" not in out


def test_preview_is_exactly_the_first_12000_chars_of_the_json_text(returning):
    value = _padded(LIMIT + 500)
    out = returning(value)()
    full = json.dumps(value)
    assert len(out["result_preview"]) == LIMIT
    assert out["result_preview"] == full[:LIMIT]
    assert full.startswith(out["result_preview"]) and out["result_preview"] != full


def test_truncation_is_deterministic(returning):
    call = returning(_padded(LIMIT + 7))
    assert call() == call()


def test_untruncated_result_has_result_key_and_no_flag(returning):
    out = returning({"k": [1, 2, "three"]})()
    assert out == {"result": {"k": [1, 2, "three"]}}


def test_length_is_counted_on_the_escaped_json_text(returning):
    # json.dumps escapes "é" as "\u00e9" (6 chars), so the text is much longer than the value.
    value = {"s": "é" * 2000}
    full = json.dumps(value)
    assert len(full) > LIMIT and len(value["s"]) < LIMIT
    out = returning(value)()
    assert out["result_truncated"] is True
    assert out["result_preview"] == full[:LIMIT]


def test_truncation_applies_to_a_list_result_too(returning):
    value = ["y" * 100] * 200   # json text is well over 12000
    full = json.dumps(value)
    assert len(full) > LIMIT
    out = returning(value)()
    assert out == {"result_truncated": True, "result_preview": full[:LIMIT]}


# ---- non-finite floats become strings before json.dumps ----
def test_nan_and_infinities_become_strings_in_a_dict(returning):
    out = returning({"a": float("nan"), "b": float("inf"), "c": float("-inf")})()
    assert out == {"result": {"a": "nan", "b": "inf", "c": "-inf"}}


def test_nan_inside_nested_list_becomes_string(returning):
    out = returning({"xs": [1.5, float("nan"), [float("inf")]]})()
    assert out == {"result": {"xs": [1.5, "nan", ["inf"]]}}


def test_top_level_nonfinite_float_result(returning):
    assert returning(float("nan"))() == {"result": "nan"}
    assert returning(float("-inf"))() == {"result": "-inf"}


def test_finite_floats_and_ints_are_unchanged(returning):
    out = returning({"f": 1.5, "i": 3, "z": 0.0, "n": -2.25})()
    assert out == {"result": {"f": 1.5, "i": 3, "z": 0.0, "n": -2.25}}


def test_result_with_nonfinite_is_valid_strict_json(returning):
    out = returning({"a": float("nan"), "b": [float("inf")]})()
    text = json.dumps(out, allow_nan=False)   # would raise ValueError if NaN/Infinity survived
    assert json.loads(text) == out


def test_nonfinite_string_forms_count_toward_the_limit(returning):
    # many NaNs become the 3-char string "nan" (5 chars with quotes and comma+space), then truncate
    value = [float("nan")] * 4000
    shaped = json.dumps(["nan"] * 4000)
    assert len(shaped) > LIMIT
    out = returning(value)()
    assert out == {"result_truncated": True, "result_preview": shaped[:LIMIT]}
