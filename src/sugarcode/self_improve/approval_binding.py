"""Rollback approval target binding (SC-A01 prep, additions-only).

Vulnerability under repair: ``SelfImprovementEngine.rollback()`` checks only
that the gate decision for the supplied approval id is ``approved``. Unlike
``activate()`` - which compares the approval id recorded on the registry
proposal - rollback never verifies the approval was requested for this
feature, this module, or the rollback action at all. Any approved gate
record (an activation approval, or a rollback approval requested for a
different feature or module) can be replayed to roll back an arbitrary
active feature.

This module is the pure binding validator prepared for that repair. It has
no I/O of its own beyond an injected record source and edits nothing; the
engine/gate wiring belongs to the integration owner. The integration
contract and open decisions live in docs/approval-rollback-binding.md.

Scope limits: this is metadata matching only. It is not actor
authentication, cryptographic authority, or proof of human intent. A local
actor who can write the gate file can still fabricate a well-formed
approved record; binding validation cannot and does not replace human
authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Protocol, runtime_checkable

ROLLBACK_ACTION = "self_improvement_rollback"
ACTIVATION_ACTION = "self_improvement_activation"

# Payload key written by engine.request_rollback(); the SC-J05 schema must
# freeze this exact key for binding to remain enforceable.
FEATURE_PAYLOAD_KEY = "feature"

# Optional payload key for version-pinned rollback requests. Nothing writes
# it yet; populating it requires the integration-side request_rollback()
# change documented in docs/approval-rollback-binding.md.
VERSION_PAYLOAD_KEY = "active_version_at_request"


class ApprovalBindingError(ValueError):
    """Base class for rollback approval binding failures."""


class InvalidApprovalRecord(ApprovalBindingError):
    """The stored record lacks the shape binding validation requires."""


class ApprovalBindingMismatch(ApprovalBindingError):
    """A well-formed approval binds to a different target than requested."""


@dataclass(frozen=True)
class BindingReport:
    """The target a record was verified to bind to."""

    module_id: int
    module_slug: str
    action_type: str
    feature: str
    # True only when the record pins an active version and it matched.
    version_bound: bool


@runtime_checkable
class ApprovalRecordSource(Protocol):
    """PROPOSED minimal full-record read API, pending the SC-J05 contract.

    The peer-owned SC-J05 request/status schema and read API must expose at
    least this: return the complete stored record for an approval id as a
    mapping, raising KeyError for an unknown id and the J05 schema error
    type for a record that fails schema validation. This protocol is a
    documented proposal for that contract, not the frozen interface; the
    validator itself depends only on the mapping it is handed.
    """

    def record(self, approval_id: str) -> Mapping[str, Any]: ...


def _require_str(value: Any, field: str) -> str:
    if type(value) is not str:
        raise InvalidApprovalRecord(
            f"approval record field {field!r} must be a string, "
            f"got {type(value).__name__}")
    return value


def _require_module_id(value: Any) -> int:
    # type(...) is int excludes bool, which is an int subclass but never a
    # valid module identity.
    if type(value) is not int:
        raise InvalidApprovalRecord(
            f"approval record field 'module_id' must be an integer, "
            f"got {type(value).__name__}")
    return value


def rollback_target(record: Mapping[str, Any]) -> BindingReport:
    """Extract and shape-check the binding target of a stored record.

    Raises InvalidApprovalRecord for a non-mapping record, missing required
    keys, wrong field types, or a malformed payload. Unknown extra keys are
    tolerated so newer records remain readable. The record's decision
    status is deliberately NOT inspected here: status is the gate's
    decision check and the SC-J05 schema's concern, not binding's.
    """
    if not isinstance(record, Mapping):
        raise InvalidApprovalRecord(
            f"approval record must be a mapping, got {type(record).__name__}")
    missing = [k for k in ("module_id", "module_slug", "action_type", "payload")
               if k not in record]
    if missing:
        raise InvalidApprovalRecord(
            f"approval record missing required fields: {', '.join(missing)}")
    module_id = _require_module_id(record["module_id"])
    module_slug = _require_str(record["module_slug"], "module_slug")
    action_type = _require_str(record["action_type"], "action_type")
    payload = record["payload"]
    if not isinstance(payload, Mapping):
        raise InvalidApprovalRecord(
            f"approval record field 'payload' must be a mapping, "
            f"got {type(payload).__name__}")
    feature = payload.get(FEATURE_PAYLOAD_KEY)
    if action_type == ROLLBACK_ACTION:
        feature = _require_str(feature, f"payload.{FEATURE_PAYLOAD_KEY}")
    elif feature is not None:
        feature = _require_str(feature, f"payload.{FEATURE_PAYLOAD_KEY}")
    return BindingReport(module_id=module_id, module_slug=module_slug,
                         action_type=action_type, feature=feature or "",
                         version_bound=False)


def validate_rollback_binding(record: Mapping[str, Any], *, module_id: int,
                              module_slug: str, feature_name: str,
                              current_active_version: Optional[int] = None
                              ) -> BindingReport:
    """Verify a stored approval binds to this exact rollback target.

    Raises ApprovalBindingMismatch when the record is well-formed but was
    requested for a different action, module, or feature - the replay case
    the engine currently permits. Raises InvalidApprovalRecord when the
    record lacks the shape binding requires. Returns the BindingReport on
    success.

    Version binding: if the record's payload pins
    ``active_version_at_request``, the caller MUST supply
    ``current_active_version`` and the two must agree; a feature that moved
    to a newer version since the human approved is a different target. If
    the record pins no version (all records written today), the result has
    ``version_bound=False`` - a documented weaker binding, not an error.
    """
    if type(module_id) is not int:
        raise TypeError("module_id must be an int")
    if type(module_slug) is not str:
        raise TypeError("module_slug must be a str")
    if type(feature_name) is not str:
        raise TypeError("feature_name must be a str")
    if current_active_version is not None and type(current_active_version) is not int:
        raise TypeError("current_active_version must be an int or None")

    target = rollback_target(record)
    if target.action_type != ROLLBACK_ACTION:
        raise ApprovalBindingMismatch(
            f"approval is for action {target.action_type!r}, "
            f"not {ROLLBACK_ACTION!r}")
    if target.module_id != module_id or target.module_slug != module_slug:
        raise ApprovalBindingMismatch(
            f"approval is for module {target.module_id}/{target.module_slug!r}, "
            f"not {module_id}/{module_slug!r}")
    if target.feature != feature_name:
        raise ApprovalBindingMismatch(
            f"approval is for feature {target.feature!r}, not {feature_name!r}")

    payload = record["payload"]
    version_bound = False
    if VERSION_PAYLOAD_KEY in payload:
        pinned = payload[VERSION_PAYLOAD_KEY]
        if pinned is not None and type(pinned) is not int:
            raise InvalidApprovalRecord(
                f"approval record field 'payload.{VERSION_PAYLOAD_KEY}' must be "
                f"an integer or null, got {type(pinned).__name__}")
        if current_active_version is None and pinned is not None:
            raise ApprovalBindingError(
                "approval pins an active version; caller must supply "
                "current_active_version to validate the binding")
        if pinned != current_active_version:
            raise ApprovalBindingMismatch(
                f"approval pins active version {pinned!r}, but the feature's "
                f"current active version is {current_active_version!r}; the "
                f"human approved a different state")
        version_bound = pinned is not None
    return BindingReport(module_id=target.module_id, module_slug=target.module_slug,
                         action_type=target.action_type, feature=target.feature,
                         version_bound=version_bound)


def validate_rollback_request(source: ApprovalRecordSource, approval_id: str, *,
                              module_id: int, module_slug: str, feature_name: str,
                              current_active_version: Optional[int] = None
                              ) -> BindingReport:
    """Fetch a record through the J05 read API and validate its binding.

    KeyError for an unknown approval id propagates from the source; the
    SC-J05 schema error for an invalid stored record propagates as well.
    """
    if type(approval_id) is not str:
        raise TypeError("approval_id must be a str")
    return validate_rollback_binding(
        source.record(approval_id), module_id=module_id, module_slug=module_slug,
        feature_name=feature_name, current_active_version=current_active_version)
