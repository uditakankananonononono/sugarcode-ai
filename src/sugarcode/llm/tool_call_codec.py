"""Strict decoding and guarded execution for model tool calls (G02 prep).

AUTHORED, NOT RUN, NOT WIRED. Independent public module: stdlib only, imports
nothing from the repo and shares no helpers with self_improve.isolated_result_codec.

decode_tool_arguments(arguments, max_chars, max_depth=64) -> dict
    arguments: JSON text, or an already-built dict. "" and whitespace-only text
    (JSON whitespace) mean {} (provider compatibility). Anything else that is
    neither str nor dict is refused as not_text.
    A direct dict is NOT parsed and is returned as the same object, but it is NOT
    unvalidated: it goes through the same iterative walk (depth ceiling, a node
    count cap of max_chars, str keys at every level, lists/tuples treated as
    containers), so cycles and shared-reference blowups end in too_deep/too_large.
    For text, rejects: text over max_chars, invalid JSON (including the int digit-limit
    ValueError and RecursionError), duplicate object keys at any depth, NaN /
    Infinity / -Infinity and overflowing floats such as 1e999 (rejected, never
    coerced), a top level that is not an object, and nesting deeper than
    max_depth (the top-level object is depth 1). No process limits.
    Cap misuse (bool / non-int, max_chars < 1, max_depth outside 1..64) raises
    plain TypeError / ValueError, NOT ToolCallDecodeError.

decode_strict_json(text, max_chars, max_depth=64, root="any") -> value   (H04a, additive)
    Same parser, caps and walk as decode_tool_arguments, for text only; root "object" | "array" | "any".
    Blank text is invalid_json (not {}). decode_tool_arguments is a thin caller and its behavior is unchanged.

guarded_call(fn, *args, **kwargs) -> {"result": value} | {"error": "Type: message"}
    Runs fn and turns any Exception (including ImportError, AttributeError,
    RecursionError, MemoryError) into an error dict. BaseException (KeyboardInterrupt,
    SystemExit) propagates. The message is capped at MAX_ERROR_CHARS.

The digit-limit catch relies on ValueError being what int() raises past the
interpreter's int-string limit; grounded only in the peer's Python 3.10.12 /
4300-digit environment.
"""
from __future__ import annotations

import json
import math

__all__ = ["DEFAULT_MAX_CHARS", "DEFAULT_MAX_DEPTH", "MAX_ERROR_CHARS", "ToolCallDecodeError",
           "decode_strict_json", "decode_tool_arguments", "guarded_call"]

DEFAULT_MAX_CHARS = 65_536  # author choice for callers; decode_tool_arguments still requires max_chars
DEFAULT_MAX_DEPTH = 64
MAX_ERROR_CHARS = 500  # author choice
_ROOTS = ("object", "array", "any")


class ToolCallDecodeError(ValueError):
    """Tool arguments refused. `reason` is one of: not_text, too_large, invalid_json,
    duplicate_key, non_finite, too_deep, not_object, not_array, non_string_key."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"invalid tool arguments: {reason}")
        self.reason = reason


def _check_cap(name: str, value, low: int, high: int | None = None) -> None:
    if type(value) is not int:
        raise TypeError(f"{name} must be an int")
    if value < low or (high is not None and value > high):
        raise ValueError(f"{name} out of range")


def _reject_constant(_name: str):
    raise ToolCallDecodeError("non_finite")


def _parse_float(text: str) -> float:
    value = float(text)
    if not math.isfinite(value):
        raise ToolCallDecodeError("non_finite")
    return value


def _pairs(pairs: list) -> dict:
    out: dict = {}
    for key, value in pairs:
        if key in out:
            raise ToolCallDecodeError("duplicate_key")
        out[key] = value
    return out


def _walk(root, max_depth: int, max_nodes: int) -> str | None:
    """Iterative check of a built structure. Returns a ToolCallDecodeError reason or None.
    Root is depth 1; every value visited counts as a node (cycles and shared-reference
    fan-out end at the depth or node cap, never loop)."""
    stack = [(root, 1)]
    nodes = 1
    while stack:
        node, depth = stack.pop()
        if depth > max_depth:
            return "too_deep"
        if isinstance(node, dict):
            if not all(isinstance(k, str) for k in node):
                return "non_string_key"
            children = list(node.values())
        elif isinstance(node, (list, tuple)):
            children = list(node)
        else:
            continue
        nodes += len(children)
        if nodes > max_nodes:
            return "too_large"
        stack.extend((c, depth + 1) for c in children if isinstance(c, (dict, list, tuple)))
    return None


def decode_strict_json(text, max_chars, max_depth=DEFAULT_MAX_DEPTH, root="any"):
    """Strictly decode JSON text (H04a). Same parser policy as decode_tool_arguments.

    root: "object" (dict only), "array" (list only) or "any". Any other root value, and cap
    misuse, raise plain TypeError / ValueError, NOT ToolCallDecodeError. Non-str text is
    refused as not_text; text over max_chars as too_large (checked before parsing); blank or
    whitespace-only text is refused as invalid_json (NOT mapped to {}). Also rejects invalid
    JSON, duplicate keys, NaN/Infinity/overflowing floats, nesting deeper than max_depth
    (top level is depth 1) and a node count over max_chars. A root of the wrong kind raises
    not_object (root="object") or not_array (root="array"). Returns the decoded value.
    """
    _check_cap("max_chars", max_chars, 1)
    _check_cap("max_depth", max_depth, 1, DEFAULT_MAX_DEPTH)
    if root not in _ROOTS:
        raise ValueError("root must be one of 'object', 'array', 'any'")
    if not isinstance(text, str):
        raise ToolCallDecodeError("not_text")
    if len(text) > max_chars:
        raise ToolCallDecodeError("too_large")
    try:
        value = json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant,
                           parse_float=_parse_float)
    except ToolCallDecodeError:
        raise
    except RecursionError:
        raise ToolCallDecodeError("too_deep") from None
    except ValueError:  # JSONDecodeError (blank text included) and the int digit-limit ValueError
        raise ToolCallDecodeError("invalid_json") from None
    if root == "object" and not isinstance(value, dict):
        raise ToolCallDecodeError("not_object")
    if root == "array" and not isinstance(value, list):
        raise ToolCallDecodeError("not_array")
    reason = _walk(value, max_depth, max_chars)
    if reason is not None:
        raise ToolCallDecodeError(reason)
    return value


def decode_tool_arguments(arguments, max_chars, max_depth=DEFAULT_MAX_DEPTH) -> dict:
    """Decode model-supplied tool arguments strictly; see module docstring."""
    _check_cap("max_chars", max_chars, 1)
    _check_cap("max_depth", max_depth, 1, DEFAULT_MAX_DEPTH)
    if isinstance(arguments, dict):
        reason = _walk(arguments, max_depth, max_chars)
        if reason is not None:
            raise ToolCallDecodeError(reason)
        return arguments
    if not isinstance(arguments, str):
        raise ToolCallDecodeError("not_text")
    if len(arguments) > max_chars:
        raise ToolCallDecodeError("too_large")
    if arguments.strip(" \t\n\r") == "":
        return {}
    return decode_strict_json(arguments, max_chars, max_depth, root="object")


def guarded_call(fn, *args, **kwargs) -> dict:
    """Call fn(*args, **kwargs); never raises Exception. See module docstring."""
    try:
        return {"result": fn(*args, **kwargs)}
    except Exception as exc:  # noqa: BLE001 - boundary: surface as data
        try:
            message = str(exc)
        except Exception:  # noqa: BLE001
            message = ""
        return {"error": f"{type(exc).__name__}: {message}"[:MAX_ERROR_CHARS + 60]}
