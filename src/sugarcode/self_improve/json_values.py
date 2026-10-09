"""Bounded JSON snapshots for telemetry and generated-test samples."""
from __future__ import annotations

import math
from typing import Any


class InvalidTelemetryValue(ValueError):
    """Input cannot be represented by the bounded telemetry contract."""


def snapshot_json(value: Any) -> Any:
    """Copy exact builtins only, without calling user conversion methods.

    Tuples become arrays. Shared noncyclic containers are allowed. Limits
    count expanded values, not distinct objects, so alias expansion is bounded.
    """
    active: set[int] = set()
    remaining = 10_000

    def visit(item: Any, depth: int) -> Any:
        nonlocal remaining
        remaining -= 1
        if remaining < 0 or depth > 64:
            raise InvalidTelemetryValue("telemetry size or depth limit exceeded")
        kind = type(item)
        if item is None or kind in (str, bool, int):
            return item
        if kind is float:
            if not math.isfinite(item):
                raise InvalidTelemetryValue("nonfinite telemetry number")
            return item
        if kind not in (list, tuple, dict):
            raise InvalidTelemetryValue("unsupported telemetry value type")
        identity = id(item)
        if identity in active:
            raise InvalidTelemetryValue("cyclic telemetry container")
        active.add(identity)
        try:
            if kind is dict:
                result = {}
                for key, child in item.items():
                    if type(key) is not str:
                        raise InvalidTelemetryValue("telemetry object keys must be strings")
                    result[key] = visit(child, depth + 1)
                return result
            return [visit(child, depth + 1) for child in item]
        finally:
            active.remove(identity)

    return visit(value, 0)
