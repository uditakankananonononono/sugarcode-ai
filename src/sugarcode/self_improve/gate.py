"""Approval gate for feature activation in Sugarcode.

Detection, planning, synthesis, and sandbox testing run autonomously.
Activation - new code becoming callable by a module - requires a human
decision recorded in the gate file. Sugarcode has no central approval
service, so the file-backed manual gate is the production gate here.
"""
from __future__ import annotations

import json
import math
import threading
import time
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from .atomic_file import AtomicDurabilityError, atomic_write_text
from .json_values import snapshot_json

PENDING, APPROVED, REJECTED = "pending", "approved", "rejected"


class InvalidApprovalState(ValueError):
    """Stored gate JSON is ambiguous or outside the supported JSON domain."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InvalidApprovalState("duplicate approval object key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise InvalidApprovalState("nonfinite approval number")


def _finite_float(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise InvalidApprovalState("nonfinite approval number")
    return result


class ApprovalGate(Protocol):
    def request(self, *, module_id: int, module_slug: str, action_type: str,
                summary: str, payload: dict[str, Any]) -> str: ...
    def decision(self, approval_id: str) -> str: ...


class ManualApprovalGate:
    """File-backed human gate.

    Requests persist to approvals.json. A human decides by editing the file
    or calling decide(); nothing auto-approves unless explicitly constructed
    with auto_approve=True (used by tests and local demos).
    """

    def __init__(self, path: Path, *, auto_approve: bool = False) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._auto = auto_approve
        self._lock = threading.Lock()
        if not self._path.exists():
            atomic_write_text(self._path, "{}")

    def _load(self) -> dict[str, Any]:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"),
                              object_pairs_hook=_unique_object,
                              parse_constant=_reject_constant,
                              parse_float=_finite_float)
            if type(data) is not dict:
                raise InvalidApprovalState("approval state must be an object")
            return data
        except (ValueError, TypeError, RecursionError) as exc:
            raise InvalidApprovalState("invalid stored approval JSON; repair required") from exc

    def _save(self, data: dict[str, Any]) -> None:
        try:
            snapshot = snapshot_json(data)
            encoded = json.dumps(snapshot, indent=2, sort_keys=True, allow_nan=False)
        except (ValueError, TypeError, RecursionError) as exc:
            raise InvalidApprovalState("invalid approval JSON write; state unchanged") from exc
        atomic_write_text(self._path, encoded)

    def request(self, *, module_id: int, module_slug: str, action_type: str,
                summary: str, payload: dict[str, Any]) -> str:
        approval_id = f"si-{uuid4().hex[:12]}"
        with self._lock:
            data = self._load()
            data[approval_id] = {
                "module_id": module_id, "module_slug": module_slug,
                "action_type": action_type, "summary": summary, "payload": payload,
                "status": APPROVED if self._auto else PENDING,
                "requested_at": time.time(), "decided_at": None,
            }
            try:
                self._save(data)
            except AtomicDurabilityError as exc:
                # Replacement landed: caller needs the generated identity to reconcile.
                exc.approval_id = approval_id
                raise
        return approval_id

    def decide(self, approval_id: str, decision: str, *, decided_by: str = "human") -> None:
        if decision not in (APPROVED, REJECTED):
            raise ValueError(f"decision must be approved or rejected, got {decision!r}")
        with self._lock:
            data = self._load()
            if approval_id not in data:
                raise KeyError(f"unknown approval {approval_id!r}")
            data[approval_id]["status"] = decision
            data[approval_id]["decided_at"] = time.time()
            data[approval_id]["decided_by"] = decided_by
            self._save(data)

    def decision(self, approval_id: str) -> str:
        with self._lock:
            data = self._load()
        if approval_id not in data:
            raise KeyError(f"unknown approval {approval_id!r}")
        return data[approval_id]["status"]
