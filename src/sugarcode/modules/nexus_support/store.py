"""Ticket store for Nexus Support (additive module, new file only).

Persists the tickets that ``triage`` produces, enforces a lifecycle state
machine, and computes first-response SLA status with exact integer-microsecond
arithmetic.  It is bookkeeping around the existing deterministic triage; it
does not send messages, contact users, or call any external service.

Trust boundary: ``loads`` checks types, legal ordered history, aware timestamps
and that ``response_due_at == submitted_at + sla_hours`` and
``submitted_at == history[0].at``.  The remaining fields (classification,
priority, routed_to, tier, inquiry text) are caller-trusted bookkeeping: they are
type-checked but not recomputed from the inquiry.
"""
from __future__ import annotations

import copy
import json
import math
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from typing import Mapping

from .core import triage

STATES = ("new", "triaged", "in_progress", "waiting_customer", "resolved", "closed")
TRANSITIONS: dict[str, frozenset[str]] = {
    "new": frozenset({"triaged", "closed"}),
    "triaged": frozenset({"in_progress", "resolved", "closed"}),
    "in_progress": frozenset({"waiting_customer", "resolved"}),
    "waiting_customer": frozenset({"in_progress", "resolved", "closed"}),
    "resolved": frozenset({"in_progress", "closed"}),
    "closed": frozenset(),
}
# Moving into one of these states counts as the first response to the customer.
RESPONSE_STATES = frozenset({"in_progress", "waiting_customer", "resolved"})
MAX_TICKETS = 10_000
MAX_INQUIRY_CHARS = 20_000
MAX_DUMP_CHARS = 50_000_000
_US = timedelta(microseconds=1)


def _aware(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _micros(delta: timedelta) -> int:
    return delta // _US


class TicketStore:
    """In-memory ticket store with JSON round-tripping."""

    def __init__(self) -> None:
        self._t: dict[str, dict] = {}

    def __len__(self) -> int:
        return len(self._t)

    def __contains__(self, ticket_id: object) -> bool:
        return ticket_id in self._t

    # -- creation -----------------------------------------------------
    def open_ticket(self, inquiry: str, *, module: str | None = None,
                    tier: str = "startup", submitted_at: datetime | None = None) -> dict:
        if not isinstance(inquiry, str) or not inquiry.strip():
            raise ValueError("inquiry must be non-empty text")
        if len(inquiry) > MAX_INQUIRY_CHARS:
            raise ValueError(f"inquiry exceeds {MAX_INQUIRY_CHARS} characters")
        if len(self._t) >= MAX_TICKETS:
            raise ValueError(f"store is full ({MAX_TICKETS} tickets)")
        when = _aware(submitted_at, "submitted_at") if submitted_at is not None \
            else datetime.now(timezone.utc)
        tri = triage(inquiry, module, tier, submitted_at=when)
        tid = tri["ticket_id"]
        if tid in self._t:
            raise ValueError(f"duplicate ticket {tid}")
        # Persist the displayed SLA contract, not triage's unrounded deadline.
        due = when + timedelta(hours=tri["sla_hours"])
        self._t[tid] = {
            "ticket_id": tid, "inquiry": inquiry, "state": "new",
            "classification": tri["classification"], "priority": tri["priority"],
            "priority_score": tri["priority_score"], "tier": tri["tier_applied"],
            "routed_to": copy.deepcopy(tri["routed_to"]),
            "sla_hours": tri["sla_hours"],
            "submitted_at": when.isoformat(), "response_due_at": due.isoformat(),
            "history": [{"state": "new", "at": when.isoformat()}],
        }
        return copy.deepcopy(self._t[tid])

    def get(self, ticket_id: str) -> dict:
        if ticket_id not in self._t:
            raise KeyError(ticket_id)
        return copy.deepcopy(self._t[ticket_id])

    # -- lifecycle ----------------------------------------------------
    def transition(self, ticket_id: str, new_state: str, at: datetime) -> dict:
        # validate everything before mutating
        if ticket_id not in self._t:
            raise KeyError(ticket_id)
        rec = self._t[ticket_id]
        when = _aware(at, "at")
        if not isinstance(new_state, str):
            raise TypeError("new_state must be a string")
        if new_state not in TRANSITIONS:
            raise ValueError(f"unknown state {new_state!r}")
        if new_state not in TRANSITIONS[rec["state"]]:
            raise ValueError(f"illegal transition {rec['state']} -> {new_state}")
        if when < datetime.fromisoformat(rec["history"][-1]["at"]):
            raise ValueError("transition time precedes the previous event")
        rec["state"] = new_state
        rec["history"].append({"state": new_state, "at": when.isoformat()})
        return copy.deepcopy(rec)

    # -- SLA ----------------------------------------------------------
    @staticmethod
    def _first_response(rec: Mapping) -> datetime | None:
        for ev in rec["history"]:
            if ev["state"] in RESPONSE_STATES:
                return datetime.fromisoformat(ev["at"])
        return None

    def sla_status(self, ticket_id: str, now: datetime) -> dict:
        if ticket_id not in self._t:
            raise KeyError(ticket_id)
        rec = self._t[ticket_id]
        now_u = _aware(now, "now")
        last = datetime.fromisoformat(rec["history"][-1]["at"])
        if now_u < last:
            raise ValueError("now precedes the latest ticket event")
        due = datetime.fromisoformat(rec["response_due_at"])
        responded = self._first_response(rec)
        ref = responded if responded is not None else now_u
        margin_us = _micros(due - ref)
        hours = Fraction(margin_us, 3_600_000_000)
        return {"ticket_id": ticket_id, "responded": responded is not None,
                "first_response_at": responded.isoformat() if responded else None,
                "margin_hours": float(hours), "margin_hours_exact": str(hours),
                "breached": margin_us < 0}

    def breaches(self, now: datetime) -> list[str]:
        """Tickets whose first response was late, or is overdue at ``now``.

        Tickets whose latest event is after ``now`` are skipped (they cannot be
        evaluated at that earlier instant).
        """
        now_u = _aware(now, "now")
        out = []
        for tid, rec in self._t.items():
            if datetime.fromisoformat(rec["history"][-1]["at"]) > now_u:
                continue
            if self.sla_status(tid, now_u)["breached"]:
                out.append(tid)
        return sorted(out)

    def counts(self) -> dict[str, int]:
        out = {s: 0 for s in STATES}
        for rec in self._t.values():
            out[rec["state"]] += 1
        return out

    # -- persistence --------------------------------------------------
    def dumps(self) -> str:
        return json.dumps({"version": 1, "tickets": [self._t[k] for k in sorted(self._t)]},
                          sort_keys=True)

    @classmethod
    def loads(cls, text: str) -> "TicketStore":
        if not isinstance(text, str):
            raise TypeError("text must be str")
        if len(text) > MAX_DUMP_CHARS:
            raise ValueError("dump too large")
        try:
            doc = json.loads(text)
        except (ValueError, RecursionError) as exc:
            raise ValueError(f"invalid store JSON: {exc}") from None
        if not isinstance(doc, dict) or doc.get("version") != 1 \
                or not isinstance(doc.get("tickets"), list):
            raise ValueError("unsupported store document")
        if len(doc["tickets"]) > MAX_TICKETS:
            raise ValueError("too many tickets")
        store = cls()
        for rec in doc["tickets"]:
            store._ingest(rec)
        return store

    def _ingest(self, rec: object) -> None:
        if not isinstance(rec, dict):
            raise ValueError("ticket must be an object")
        need = {"ticket_id": str, "inquiry": str, "state": str, "classification": str,
                "priority": str, "tier": str, "submitted_at": str, "response_due_at": str,
                "history": list, "routed_to": dict}
        for key, typ in need.items():
            if not isinstance(rec.get(key), typ):
                raise ValueError(f"ticket field {key!r} missing or wrong type")
        for key in ("priority_score", "sla_hours"):
            v = rec.get(key)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                raise ValueError(f"ticket field {key!r} must be a finite number")
        if rec["state"] not in TRANSITIONS or rec["ticket_id"] in self._t:
            raise ValueError("bad state or duplicate ticket id")
        hist = rec["history"]
        if not hist or not isinstance(hist[0], dict) or hist[0].get("state") != "new":
            raise ValueError("history must start at 'new'")

        def stamp(text: object) -> datetime:
            # persisted stamps must be aware ISO-8601; naive ones are rejected
            if not isinstance(text, str):
                raise ValueError("timestamp must be text")
            try:
                dt = datetime.fromisoformat(text)
            except ValueError:
                raise ValueError("malformed timestamp") from None
            if dt.tzinfo is None or dt.utcoffset() is None:
                raise ValueError("timestamp must carry a timezone")
            return dt.astimezone(timezone.utc)

        norm = []
        prev_state, prev_at = None, None
        for ev in hist:
            if not isinstance(ev, dict) or not isinstance(ev.get("state"), str):
                raise ValueError("malformed history event")
            st, at = ev["state"], stamp(ev.get("at"))
            if prev_state is not None and (st not in TRANSITIONS.get(prev_state, ())
                                           or at < prev_at):
                raise ValueError("history is not a legal ordered path")
            if prev_state is None and st != "new":
                raise ValueError("history must start at 'new'")
            norm.append({"state": st, "at": at.isoformat()})
            prev_state, prev_at = st, at
        if prev_state != rec["state"]:
            raise ValueError("state does not match history")
        submitted = stamp(rec["submitted_at"])
        due = stamp(rec["response_due_at"])
        if submitted.isoformat() != norm[0]["at"]:
            raise ValueError("submitted_at does not match history[0]")
        if not 0 < rec["sla_hours"] <= 1_000_000:
            raise ValueError("sla_hours out of range")
        try:
            expected = submitted + timedelta(hours=rec["sla_hours"])
        except OverflowError:
            raise ValueError("sla_hours out of range") from None
        if due != expected:
            raise ValueError("response_due_at inconsistent with submitted_at + sla_hours")
        out = copy.deepcopy(rec)
        out["history"] = norm
        out["submitted_at"] = submitted.isoformat()
        out["response_due_at"] = due.isoformat()
        self._t[rec["ticket_id"]] = out
