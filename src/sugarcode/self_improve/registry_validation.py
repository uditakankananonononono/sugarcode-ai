"""SC-J02 additive preparation: strict decoding and a proposed registry schema.

No filesystem access, persistence, authority check, or production wiring.
See docs/prep/sc-j02-registry-validation.md before integration.
"""
from __future__ import annotations

import json
from .approval_consumption import CONSUMED_KEY, validate_consumptions
import math
import re
from typing import Any


class RegistryValidationError(ValueError):
    """Registry bytes or state do not satisfy the documented contract."""


_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _fail(location: str, reason: str) -> None:
    # Do not include untrusted field values, file paths or state bytes.
    raise RegistryValidationError(f"{location}: {reason}")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("JSON", "duplicate object key")
        result[key] = value
    return result


def _constant(value: str) -> None:
    _fail("JSON", "nonfinite constant")


def _float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        _fail("JSON", "nonfinite numeric value")
    return number


def _json_tree(root: Any) -> None:
    """Refuse custom objects/hooks and cycles, including in unknown fields."""
    ancestors: set[int] = set()
    stack: list[tuple[Any, bool]] = [(root, False)]
    while stack:
        value, leaving = stack.pop()
        kind = type(value)
        if leaving:
            ancestors.remove(id(value))
            continue
        if kind in (dict, list):
            identity = id(value)
            if identity in ancestors:
                _fail("state", "cyclic JSON tree")
            ancestors.add(identity)
            stack.append((value, True))
            if kind is dict:
                for key, child in value.items():
                    if type(key) is not str:
                        _fail("state", "JSON object keys must be exact strings")
                    stack.append((child, False))
            else:
                stack.extend((child, False) for child in value)
        elif kind is float:
            if not math.isfinite(value):
                _fail("state", "nonfinite numeric value")
        elif kind not in (str, int, bool, type(None)):
            _fail("state", "exact builtin JSON values required")


def _object(value: Any, location: str) -> dict[str, Any]:
    if type(value) is not dict:
        _fail(location, "object required")
    return value


def _required(obj: dict[str, Any], fields: tuple[str, ...], location: str) -> None:
    if any(field not in obj for field in fields):
        _fail(location, "missing required field")


def _text(value: Any, location: str, *, empty: bool = False) -> None:
    if type(value) is not str or (not empty and not value):
        _fail(location, "string required" if empty else "nonempty string required")


def _identifier(value: Any, location: str) -> None:
    _text(value, location)
    if not value.replace("-", "").replace("_", "").isalnum():
        _fail(location, "single-component alphanumeric identifier required")


def _integer(value: Any, location: str, *, minimum: int) -> None:
    if type(value) is not int or value < minimum:
        _fail(location, "integer outside supported domain")


def _timestamp(value: Any, location: str) -> None:
    if type(value) not in (int, float) or value < 0:
        _fail(location, "nonnegative finite timestamp required")
    # Finiteness was checked for all float values by _json_tree.


def _digest(value: Any, location: str) -> None:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        _fail(location, "lowercase SHA-256 hex digest required")


def _approval(value: Any, location: str, *, nullable: bool) -> None:
    if nullable and value is None:
        return
    _text(value, location)


def validate_registry_state(state: Any, *, expected_module: str) -> dict[str, Any]:
    """Validate exact builtin state without changing it; return the same dict.

    Unknown JSON fields are preserved. The returned object is not an immutable
    authorization token: validate again after caller edits and before effects.
    """
    _identifier(expected_module, "expected_module")
    _json_tree(state)
    root = _object(state, "state")
    _required(root, ("module", "features", "proposals"), "state")
    _identifier(root["module"], "module")
    if root["module"] != expected_module:
        _fail("module", "does not match expected module")
    if CONSUMED_KEY in root:
        try:
            validate_consumptions(root[CONSUMED_KEY])
        except ValueError as exc:
            raise RegistryValidationError("invalid engine approval consumption metadata") from exc
    features = _object(root["features"], "features")
    proposals = _object(root["proposals"], "proposals")

    for name, value in features.items():
        _identifier(name, "feature ID")
        feature = _object(value, "feature")
        _required(feature, ("versions", "active_version"), "feature")
        versions = feature["versions"]
        if type(versions) is not list:
            _fail("versions", "array required")
        for expected_version, value in enumerate(versions, 1):
            entry = _object(value, "version entry")
            _required(entry, ("version", "file", "sha256", "kind", "gap_signature",
                              "approval_id", "activated_at"), "version entry")
            _integer(entry["version"], "version", minimum=1)
            if entry["version"] != expected_version:
                _fail("version", "ordered contiguous 1-based versions required")
            _text(entry["file"], "version file")
            _digest(entry["sha256"], "version digest")
            _text(entry["kind"], "version kind")
            _text(entry["gap_signature"], "version gap_signature", empty=True)
            _approval(entry["approval_id"], "version approval_id", nullable=False)
            _timestamp(entry["activated_at"], "activated_at")
            if "dispatch_count" in entry:
                _integer(entry["dispatch_count"], "dispatch_count", minimum=0)
            for field in ("last_dispatched_at", "rolled_back_at"):
                if field in entry:
                    _timestamp(entry[field], field)
            if ("rolled_back_at" in entry) != ("rollback_approval_id" in entry):
                _fail("rollback", "rollback time and approval ID must occur together")
            if "rollback_approval_id" in entry:
                _approval(entry["rollback_approval_id"], "rollback approval_id", nullable=False)
        active = feature["active_version"]
        if active is not None:
            _integer(active, "active_version", minimum=1)
            if active > len(versions):
                _fail("active_version", "references missing version")

    for key, value in proposals.items():
        _identifier(key, "proposal ID")
        proposal = _object(value, "proposal")
        _required(proposal, ("name", "kind", "gap_signature", "code_sha256",
                             "test_sha256", "code_file", "test_file", "approval_id",
                             "status", "created_at"), "proposal")
        _identifier(proposal["name"], "proposal name")
        _text(proposal["kind"], "proposal kind")
        _text(proposal["gap_signature"], "proposal gap_signature", empty=True)
        for field in ("code_sha256", "test_sha256"):
            _digest(proposal[field], field)
        for field in ("code_file", "test_file"):
            _text(proposal[field], field)
        # Direct FeatureRegistry.activate can leave proposal approval_id null.
        _approval(proposal["approval_id"], "proposal approval_id", nullable=True)
        if type(proposal["status"]) is not str or proposal["status"] not in ("proposed", "activated"):
            _fail("proposal status", "unsupported status")
        _timestamp(proposal["created_at"], "created_at")
    return root


def decode_registry_json(raw: str | bytes, *, expected_module: str) -> dict[str, Any]:
    """Strict UTF-8 JSON decoding followed by full schema validation.

    Caller owns bounded reads (SC-F02). No file reads/writes, custom conversion,
    implicit byte encoding detection, authentication, or migration is performed.
    """
    if type(raw) is bytes:
        try:
            raw = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise RegistryValidationError("JSON: invalid UTF-8") from exc
    elif type(raw) is not str:
        _fail("JSON", "exact str or bytes required")
    try:
        state = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant,
                           parse_float=_float)
    except RegistryValidationError:
        raise
    except (ValueError, RecursionError) as exc:
        raise RegistryValidationError("JSON: malformed or unsupported document") from exc
    return validate_registry_state(state, expected_module=expected_module)
