"""Strict decoder for the isolated-dispatch child result (SC-J03 PREP).

STATUS: authored, NOT run, NOT wired. Reconciled by reading main 35998c7 isolated_dispatch.py.
self_improve/isolated_dispatch.py (base ba0eb275 was not available to the author).

Contract (as documented by the author, pending peer confirmation):
  * input: the child's complete stdout as bytes (untrusted).
  * size: len(raw) <= max_bytes (default 1 MiB = 1_048_576, the existing cap
    value as reported in the inventory; the parent keeps enforcing its own cap
    while reading, this is a second, decode-side check).
  * text: strict UTF-8, no lone surrogates anywhere (keys or values).
  * JSON: exactly one document; top level is an object whose keys are exactly
    {"result"}; no duplicate keys at any depth; no NaN/Infinity/-Infinity; no
    float that overflows to inf; integers limited to max_int_digits digits;
    nesting depth limited to max_depth.
  * output: the value of "result" (plain dict/list/str/int/float/bool/None).
  * every failure raises ResultProtocolError (single exception type, with a
    short .reason code). Nothing else escapes for malformed input.
This does not prove isolation/containment; it only validates bytes.
"""
import json
import math

DEFAULT_MAX_BYTES = 1024 * 1024
DEFAULT_MAX_DEPTH = 64
DEFAULT_MAX_INT_DIGITS = 64
RESULT_KEY = "result"


class ResultProtocolError(ValueError):
    def __init__(self, reason, detail=""):
        self.reason = reason
        self.detail = detail
        super().__init__(f"{reason}: {detail}" if detail else reason)


def _pairs_hook(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ResultProtocolError("duplicate_key", repr(key)[:80])
        out[key] = value
    return out


def _reject_constant(name):
    raise ResultProtocolError("nonfinite_constant", str(name))


def _make_parse_int(max_digits):
    def parse_int(text):
        digits = text.lstrip("-")
        if len(digits) > max_digits:
            raise ResultProtocolError("int_overflow", f"{len(digits)} digits")
        return int(text)
    return parse_int


def _parse_float(text):
    try:
        value = float(text)
    except (ValueError, OverflowError):
        raise ResultProtocolError("bad_float", text[:40])
    if not math.isfinite(value):
        raise ResultProtocolError("float_overflow", text[:40])
    return value


def _check_string(s):
    try:
        s.encode("utf-8")
    except UnicodeEncodeError:
        raise ResultProtocolError("invalid_unicode", "lone surrogate")


def _walk(root, max_depth):
    """Iterative validation: depth, string validity, exact builtin types."""
    stack = [(root, 1)]
    while stack:
        node, depth = stack.pop()
        if depth > max_depth:
            raise ResultProtocolError("too_deep", str(max_depth))
        kind = type(node)
        if kind is dict:
            for k, v in node.items():
                if type(k) is not str:
                    raise ResultProtocolError("bad_key_type")
                _check_string(k)
                stack.append((v, depth + 1))
        elif kind is list:
            for v in node:
                stack.append((v, depth + 1))
        elif kind is str:
            _check_string(node)
        elif kind is float:
            if not math.isfinite(node):
                raise ResultProtocolError("nonfinite_value")
        elif kind is int or kind is bool or node is None:
            pass
        else:
            raise ResultProtocolError("bad_value_type", kind.__name__)


def decode_child_result(raw, *, max_bytes=DEFAULT_MAX_BYTES,
                        max_depth=DEFAULT_MAX_DEPTH,
                        max_int_digits=DEFAULT_MAX_INT_DIGITS):
    """Return the validated value of the child's {"result": ...} document."""
    if type(raw) not in (bytes, bytearray):
        raise ResultProtocolError("not_bytes", type(raw).__name__)
    if len(raw) > max_bytes:
        raise ResultProtocolError("too_large", f"{len(raw)} > {max_bytes}")
    if len(raw) == 0:
        raise ResultProtocolError("empty")
    try:
        text = bytes(raw).decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ResultProtocolError("invalid_utf8", str(exc)[:80])
    try:
        doc = json.loads(
            text,
            object_pairs_hook=_pairs_hook,
            parse_constant=_reject_constant,
            parse_int=_make_parse_int(max_int_digits),
            parse_float=_parse_float,
        )
    except ResultProtocolError:
        raise
    except RecursionError:
        raise ResultProtocolError("too_deep", "parser recursion")
    except ValueError as exc:  # JSONDecodeError subclasses ValueError
        raise ResultProtocolError("malformed_json", str(exc)[:80])
    if type(doc) is not dict:
        raise ResultProtocolError("top_level_not_object", type(doc).__name__)
    if set(doc.keys()) != {RESULT_KEY}:
        raise ResultProtocolError("top_level_keys", ",".join(sorted(map(str, doc)))[:80])
    _walk(doc, max_depth)
    return doc[RESULT_KEY]
