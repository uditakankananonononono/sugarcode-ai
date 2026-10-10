"""SC-P01 PREP ONLY: pure domains, not wired into any existing template.

The contract in docs/contracts/sc_p01_parameter_domains.md defines the caller
seams and narrowed domains. No persistence, imports of generated modules, or IO.
"""
from __future__ import annotations

import math
import re
from typing import Any


class ParameterDomainError(ValueError):
    """An input is outside the explicit template domain."""


_KINDS = {
    "keyword_filter": {"keywords": [], "mode": "keep"},
    "scoring_rule": {"weights": {}, "threshold": 1.0},
    "text_transform": {"pattern": r"\s+", "replacement": " "},
    "aggregator": {"group_by": "category", "op": "count", "value_field": "value"},
    "threshold_alert": {"field": "value", "threshold": 0.0, "direction": "above"},
    "field_extractor": {"fields": {}},
}


def _fail(path: str, reason: str) -> None:
    # Never include raw values or custom object repr in diagnostics.
    raise ParameterDomainError(f"{path}: {reason}")


def _string(value: Any, path: str, *, nonempty: bool = False) -> str:
    if type(value) is not str or (nonempty and not value):
        _fail(path, "expected builtin string" + (" (nonempty)" if nonempty else ""))
    return value


def _number(value: Any, path: str) -> float:
    if type(value) not in (int, float):
        _fail(path, "expected builtin int or float, excluding bool")
    try:
        number = float(value)
    except (OverflowError, ValueError):
        _fail(path, "number not representable as finite float")
    if not math.isfinite(number):
        _fail(path, "number not finite")
    return number


def _mapping(value: Any, path: str) -> dict:
    if type(value) is not dict:
        _fail(path, "expected builtin dict")
    for key in value:
        _string(key, path + ".key", nonempty=True)
    return value


def _pattern(value: Any, path: str) -> re.Pattern:
    pattern = _string(value, path)
    try:
        return re.compile(pattern)
    except (re.error, OverflowError, RecursionError):
        _fail(path, "invalid regex")


def _choice(value: Any, choices: tuple[str, ...], path: str) -> str:
    value = _string(value, path)
    if value not in choices:
        _fail(path, "unsupported value")
    return value


def validate_parameters(kind: str, params: dict, overrides: dict | None = None) -> dict:
    """Return a fresh normalized full parameter set; overrides replace fields.

    Base is validated even if an override would hide it. Nested mappings are
    replaced, not merged. None means no overrides; {} is an explicit empty
    override mapping. Every supplied field must be known. No coercion hooks.
    """
    _string(kind, "kind")
    if kind not in _KINDS:
        _fail("kind", "unknown template")
    base = _validate_set(kind, params)
    if overrides is None:
        return base
    _mapping(overrides, "overrides")
    unknown = set(overrides) - set(_KINDS[kind])
    if unknown:
        _fail("overrides", "unknown parameter")
    return _validate_set(kind, {**base, **overrides})


def _validate_set(kind: str, supplied: dict) -> dict:
    _mapping(supplied, "params")
    if set(supplied) - set(_KINDS[kind]):
        _fail("params", "unknown parameter")
    p = {**_KINDS[kind], **supplied}
    if kind == "keyword_filter":
        if type(p["keywords"]) is not list:
            _fail("keywords", "expected builtin list")
        p["keywords"] = [_string(k, "keywords.item", nonempty=True) for k in p["keywords"]]
        folded = [k.lower() for k in p["keywords"]]
        if len(set(folded)) != len(folded):
            _fail("keywords", "case-folded duplicate")
        p["mode"] = _choice(p["mode"], ("keep", "drop"), "mode")
    elif kind == "scoring_rule":
        weights = _mapping(p["weights"], "weights")
        if len({k.lower() for k in weights}) != len(weights):
            _fail("weights", "case-folded duplicate keyword")
        p["weights"] = {k: _number(v, "weights.value") for k, v in weights.items()}
        # Bound every possible subset and every accumulation prefix, including
        # opposite signs. Conservative by design, independent of item text.
        bound = 0.0
        for weight in p["weights"].values():
            bound += abs(weight)
            if not math.isfinite(bound):
                _fail("weights", "absolute sum overflows float")
        p["threshold"] = _number(p["threshold"], "threshold")
    elif kind == "text_transform":
        pattern = _pattern(p["pattern"], "pattern")
        replacement = _string(p["replacement"], "replacement")
        try:
            pattern.sub(replacement, "")  # also parses backreference syntax
        except (re.error, IndexError):
            _fail("replacement", "invalid regex replacement")
    elif kind == "aggregator":
        p["group_by"] = _string(p["group_by"], "group_by", nonempty=True)
        p["value_field"] = _string(p["value_field"], "value_field", nonempty=True)
        p["op"] = _choice(p["op"], ("count", "sum", "mean"), "op")
    elif kind == "threshold_alert":
        p["field"] = _string(p["field"], "field", nonempty=True)
        p["threshold"] = _number(p["threshold"], "threshold")
        p["direction"] = _choice(p["direction"], ("above", "below"), "direction")
    elif kind == "field_extractor":
        fields = _mapping(p["fields"], "fields")
        for pattern in fields.values():
            _pattern(pattern, "fields.pattern")
        p["fields"] = dict(fields)
    return p


def validate_runtime_items(kind: str, items: list, effective: dict) -> None:
    """Preflight exact-list input before templates read any rows.

    Only numeric/grouping seams are covered. Does not transform input. The
    caller must prevent changes after validation and use identical parameters.
    """
    p = validate_parameters(kind, effective)
    if type(items) is not list:
        _fail("items", "expected builtin list")
    if kind not in ("aggregator", "threshold_alert"):
        return
    signatures: dict[str, tuple] = {}
    totals: dict[str, float] = {}
    for row in items:
        if type(row) is not dict:
            if isinstance(row, dict):
                _fail("items.row", "dict subclass not supported")
            continue  # preserve ordinary non-dict skip behavior
        # Reject custom keys before dictionary lookup can invoke equality hooks.
        if any(type(key) is not str for key in row):
            _fail("items.row", "expected builtin string keys")
        if kind == "threshold_alert":
            value = row.get(p["field"])
            if value is None:
                continue
            if type(value) is str:
                try:
                    number = float(value)
                except ValueError:
                    continue  # legacy nonnumeric strings are skipped
                if not math.isfinite(number):
                    _fail("items.value", "numeric string not finite")
            else:
                _number(value, "items.value")
            continue
        present = p["group_by"] in row
        group = row.get(p["group_by"], "<missing>")
        if type(group) not in (str, int, float, bool, type(None)):
            _fail("items.group", "unsupported group key")
        if type(group) in (int, float):
            _number(group, "items.group")
        label = str(group)
        signature = (present, type(group), group)
        if label in signatures and signatures[label] != signature:
            _fail("items.group", "distinct group keys have identical rendered label")
        signatures[label] = signature
        if p["op"] == "count":
            continue
        value = row.get(p["value_field"])
        if type(value) is bool:
            _fail("items.value", "bool is not an aggregation number")
        if type(value) in (int, float):
            number = _number(value, "items.value")
            total = totals.get(label, 0.0) + number
            if not math.isfinite(total):
                _fail("items.value", "group sum overflows float")
            totals[label] = total
        elif isinstance(value, (int, float)):
            _fail("items.value", "numeric subclass not supported")
        # Other nonnumeric values retain the template's skip behavior.
