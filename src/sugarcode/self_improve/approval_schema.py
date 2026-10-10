"""Approval request/status schema checks (SC-J05 prep helper).

Pure functions over an already-decoded approval record (one value of the
approvals.json object). Nothing here reads or writes files, imports gate or
engine, or calls the gate. Integration (calling these from
ManualApprovalGate.request/decision/decide and from engine.activate/rollback)
is NOT done by this module.

Scope: shape, status and action/module/candidate/hash/feature identity.
This does NOT authenticate a human or whoever edited the file; a matching
record proves only that the stored fields agree with the requested operation.

Interface assumed from SC-J04 (peer-owned, read at main 35998c7, not defined
here): the writer snapshots exact builtins only (tuples become arrays), finite
numbers, string keys; the reader refuses duplicate keys and nonfinite numbers.
J04 adds no semantic schema, so this module is the only shape check. These checks still use exact type tests, so a
non-builtin subclass is refused rather than trusted.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

PENDING, APPROVED, REJECTED = "pending", "approved", "rejected"
STATUSES = (PENDING, APPROVED, REJECTED)
ACTIVATION_ACTION = "self_improvement_activation"
ROLLBACK_ACTION = "self_improvement_rollback"

RECORD_REQUIRED = frozenset({"module_id", "module_slug", "action_type", "summary",
                             "payload", "status", "requested_at", "decided_at"})
RECORD_OPTIONAL = frozenset({"decided_by"})
ACTIVATION_PAYLOAD_KEYS = frozenset({"candidate_key", "name", "kind",
                                     "code_sha256", "gap_signature"})
ROLLBACK_PAYLOAD_KEYS = frozenset({"feature"})
_SHA256 = re.compile(r"[0-9a-f]{64}")


class ApprovalSchemaError(ValueError):
    """Record shape, status or identity does not satisfy the operation.

    `code` is a short stable reason; `str(exc)` never includes payload values.
    """

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class ActivationExpectation:
    module_id: int
    module_slug: str
    candidate_key: str
    name: str
    kind: str
    code_sha256: str
    gap_signature: str


@dataclass(frozen=True)
class RollbackExpectation:
    module_id: int
    module_slug: str
    feature: str


def _is_int(v: Any) -> bool:
    return type(v) is int


def _is_number(v: Any) -> bool:
    return (type(v) is int) or (type(v) is float and math.isfinite(v))


def _nonempty_str(v: Any) -> bool:
    return type(v) is str and v != ""


def validate_record(record: Any, *, allow_unrecorded_decision: bool = False) -> dict[str, Any]:
    """Return `record` unchanged if its envelope is well formed, else raise.

    allow_unrecorded_decision: auto_approve gates write status "approved" with
    decided_at None and no decided_by. Default False refuses that shape.
    """
    if type(record) is not dict:
        raise ApprovalSchemaError("record_not_object")
    keys = set(record)
    if any(type(k) is not str for k in keys):
        raise ApprovalSchemaError("record_key_type")
    if not RECORD_REQUIRED <= keys:
        raise ApprovalSchemaError("record_missing_field")
    if keys - RECORD_REQUIRED - RECORD_OPTIONAL:
        raise ApprovalSchemaError("record_unexpected_field")
    if not _is_int(record["module_id"]):
        raise ApprovalSchemaError("module_id_type")
    if not _nonempty_str(record["module_slug"]):
        raise ApprovalSchemaError("module_slug_type")
    if not _nonempty_str(record["action_type"]):
        raise ApprovalSchemaError("action_type_type")
    if type(record["summary"]) is not str:
        raise ApprovalSchemaError("summary_type")
    if type(record["payload"]) is not dict:
        raise ApprovalSchemaError("payload_type")
    status = record["status"]
    if type(status) is not str or status not in STATUSES:
        raise ApprovalSchemaError("status_invalid")
    if not _is_number(record["requested_at"]):
        raise ApprovalSchemaError("requested_at_type")
    decided_at = record["decided_at"]
    if decided_at is not None and not _is_number(decided_at):
        raise ApprovalSchemaError("decided_at_type")
    # SC-J04 contract (peer, main 35998c7): decide(decided_by=None) is accepted
    # and written as null, so null is a valid stored value; other types are not.
    if ("decided_by" in record and record["decided_by"] is not None
            and not _nonempty_str(record["decided_by"])):
        raise ApprovalSchemaError("decided_by_type")
    if status == PENDING:
        if decided_at is not None or "decided_by" in record:
            raise ApprovalSchemaError("pending_has_decision")
    else:
        recorded = decided_at is not None and "decided_by" in record
        if not recorded:
            partial = decided_at is not None or "decided_by" in record
            if partial or not allow_unrecorded_decision:
                raise ApprovalSchemaError("decision_not_recorded")
    return record


def validate_payload(action_type: str, payload: Any) -> dict[str, Any]:
    """Check the payload shape for a known action type."""
    if type(payload) is not dict:
        raise ApprovalSchemaError("payload_type")
    if any(type(k) is not str for k in payload):
        raise ApprovalSchemaError("payload_key_type")
    if action_type == ACTIVATION_ACTION:
        want = ACTIVATION_PAYLOAD_KEYS
    elif action_type == ROLLBACK_ACTION:
        want = ROLLBACK_PAYLOAD_KEYS
    else:
        raise ApprovalSchemaError("action_unknown")
    if action_type == ROLLBACK_ACTION and "active_version_at_request" in payload:
        pin = payload["active_version_at_request"]
        if type(pin) is not int or pin <= 0:
            raise ApprovalSchemaError("version_pin_type")
        want = want | {"active_version_at_request"}
    if set(payload) != want:
        raise ApprovalSchemaError("payload_keys")
    for key in want - {"active_version_at_request"}:
        if not _nonempty_str(payload[key]):
            raise ApprovalSchemaError("payload_field_type")
    if action_type == ACTIVATION_ACTION and not _SHA256.fullmatch(payload["code_sha256"]):
        raise ApprovalSchemaError("code_sha256_format")
    return payload


def check_binding(record: Any, expected: ActivationExpectation | RollbackExpectation,
                  *, allow_unrecorded_decision: bool = False) -> str:
    """Validate the record and bind it to one operation; return its status.

    Raises ApprovalSchemaError on any shape or identity mismatch. The returned
    status may still be pending or rejected; use require_approved to gate.
    """
    validate_record(record, allow_unrecorded_decision=allow_unrecorded_decision)
    if type(expected) is ActivationExpectation:
        action = ACTIVATION_ACTION
    elif type(expected) is RollbackExpectation:
        action = ROLLBACK_ACTION
    else:
        raise ApprovalSchemaError("expectation_type")
    if record["action_type"] != action:
        raise ApprovalSchemaError("action_mismatch")
    payload = validate_payload(action, record["payload"])
    if record["module_id"] != expected.module_id:
        raise ApprovalSchemaError("module_id_mismatch")
    if record["module_slug"] != expected.module_slug:
        raise ApprovalSchemaError("module_slug_mismatch")
    if action == ACTIVATION_ACTION:
        for field in ("candidate_key", "name", "kind", "code_sha256", "gap_signature"):
            if payload[field] != getattr(expected, field):
                raise ApprovalSchemaError(f"{field}_mismatch")
    elif payload["feature"] != expected.feature:
        raise ApprovalSchemaError("feature_mismatch")
    return record["status"]


def require_approved(record: Any, expected: ActivationExpectation | RollbackExpectation,
                     *, allow_unrecorded_decision: bool = False) -> None:
    """Raise unless the record is well formed, bound to `expected`, and approved.

    Wrong-binding errors are ApprovalSchemaError; a well-formed record that is
    pending or rejected raises PermissionError, matching engine.activate.
    """
    status = check_binding(record, expected,
                           allow_unrecorded_decision=allow_unrecorded_decision)
    if status != APPROVED:
        raise PermissionError(f"operation requires an approved gate decision, got {status!r}")
