"""UNIT B decision envelope/time semantics - AUTHORED, NOT RUN (PREP-NORUN).

No case here has been executed by the author; our side executes in audit and
reports actual counts. TestCurrentDecideEnvelope asserts CURRENT behavior at
base 6e1a421 (code-reading claims made falsifiable); those cases are expected
to PASS at base and their failure would mean the envelope semantics changed.
TestProposedFingerprintContract and TestProposedTransitionContract carry
TEST-LOCAL reference implementations of the proposed semantics from
docs/prep/unit-b-decision-envelope-compat-contract.md; they test no product
code and exist so the proposal is executable the day it is implemented.
Reference: docs/prep/unit-b-decision-envelope-report.md.
"""
import hashlib
import inspect
import json

import pytest

from sugarcode.self_improve.approval_consumption import CONSUMED_KEY
from sugarcode.self_improve.engine import SelfImprovementEngine
from sugarcode.self_improve.gate import (
    APPROVED,
    PENDING,
    REJECTED,
    ManualApprovalGate,
)
from sugarcode.self_improve.json_values import InvalidTelemetryValue, snapshot_json

MODULE_ID = 3
MODULE_SLUG = "grants"


def _request(gate, **payload):
    return gate.request(module_id=MODULE_ID, module_slug=MODULE_SLUG,
                        action_type="self_improvement_rollback", summary="x",
                        payload=payload or {"feature": "f"})


def _write_gate_file(path, records):
    path.write_text(json.dumps(records), encoding="utf-8")


class TestCurrentDecideEnvelope:
    """Current semantics at base 6e1a421, asserted as falsifiable readings."""

    def test_decide_flips_approved_to_rejected_rewriting_envelope(self, tmp_path):
        gate = ManualApprovalGate(tmp_path / "approvals.json")
        aid = _request(gate)
        gate.decide(aid, APPROVED, decided_by="reviewer-1")
        first = gate.record(aid)
        gate.decide(aid, REJECTED, decided_by="reviewer-2")
        second = gate.record(aid)
        assert second["status"] == REJECTED
        assert second["decided_by"] == "reviewer-2"
        assert second["decided_at"] >= first["decided_at"]
        assert first["requested_at"] == second["requested_at"]

    def test_decide_flips_rejected_to_approved(self, tmp_path):
        gate = ManualApprovalGate(tmp_path / "approvals.json")
        aid = _request(gate)
        gate.decide(aid, REJECTED, decided_by="reviewer-1")
        gate.decide(aid, APPROVED, decided_by="reviewer-2")
        assert gate.decision(aid) == APPROVED

    def test_redecide_same_decision_overwrites_decided_at_and_actor(self, tmp_path):
        gate = ManualApprovalGate(tmp_path / "approvals.json")
        aid = _request(gate)
        gate.decide(aid, APPROVED, decided_by="reviewer-1")
        gate.decide(aid, APPROVED, decided_by="reviewer-2")
        record = gate.record(aid)
        assert record["status"] == APPROVED
        assert record["decided_by"] == "reviewer-2"

    def test_no_decision_history_survives_multiple_decides(self, tmp_path):
        gate = ManualApprovalGate(tmp_path / "approvals.json")
        aid = _request(gate)
        gate.decide(aid, APPROVED, decided_by="reviewer-1")
        gate.decide(aid, REJECTED, decided_by="reviewer-2")
        gate.decide(aid, APPROVED, decided_by="reviewer-3")
        record = gate.record(aid)
        # Only the latest decision exists; the envelope carries no history key.
        assert set(record) == {"module_id", "module_slug", "action_type", "summary",
                               "payload", "status", "requested_at", "decided_at",
                               "decided_by"}
        assert record["decided_by"] == "reviewer-3"

    def test_requested_at_after_decided_at_accepted(self, tmp_path):
        path = tmp_path / "approvals.json"
        _write_gate_file(path, {"si-x": {
            "module_id": MODULE_ID, "module_slug": MODULE_SLUG,
            "action_type": "self_improvement_activation", "summary": "x",
            "payload": {}, "status": PENDING,
            "requested_at": 9e18, "decided_at": None}})
        gate = ManualApprovalGate(path)
        gate.decide("si-x", APPROVED, decided_by="reviewer-1")
        record = gate.record("si-x")
        # decide succeeded and stored decided_at EARLIER than requested_at:
        # no requested_at <= decided_at ordering is enforced.
        assert record["status"] == APPROVED
        assert record["requested_at"] > record["decided_at"]

    def test_negative_requested_at_accepted(self, tmp_path):
        path = tmp_path / "approvals.json"
        _write_gate_file(path, {"si-neg": {
            "module_id": MODULE_ID, "module_slug": MODULE_SLUG,
            "action_type": "self_improvement_activation", "summary": "x",
            "payload": {}, "status": PENDING,
            "requested_at": -5, "decided_at": None}})
        gate = ManualApprovalGate(path)
        gate.decide("si-neg", APPROVED)
        assert gate.record("si-neg")["requested_at"] == -5

    def test_far_future_decided_at_accepted(self, tmp_path):
        path = tmp_path / "approvals.json"
        _write_gate_file(path, {"si-future": {
            "module_id": MODULE_ID, "module_slug": MODULE_SLUG,
            "action_type": "self_improvement_activation", "summary": "x",
            "payload": {}, "status": APPROVED,
            "requested_at": 1.0, "decided_at": 9e18, "decided_by": "reviewer-1"}})
        gate = ManualApprovalGate(path)
        assert gate.decision("si-future") == APPROVED
        assert gate.record("si-future")["decided_at"] == 9e18

    def test_null_actor_accepted_and_stored_null(self, tmp_path):
        gate = ManualApprovalGate(tmp_path / "approvals.json")
        aid = _request(gate)
        gate.decide(aid, APPROVED, decided_by=None)
        record = gate.record(aid)
        assert record["status"] == APPROVED
        assert record["decided_by"] is None

    def test_status_only_legacy_record_decidable_and_flippable(self, tmp_path):
        path = tmp_path / "approvals.json"
        _write_gate_file(path, {"si-legacy": {"status": PENDING}})
        gate = ManualApprovalGate(path)
        gate.decide("si-legacy", APPROVED, decided_by="reviewer-1")
        gate.decide("si-legacy", REJECTED, decided_by="reviewer-2")
        record = gate.record("si-legacy")
        assert record["status"] == REJECTED
        assert set(record) == {"status", "decided_at", "decided_by"}
        assert gate.decision("si-legacy") == REJECTED

    def test_payload_edited_between_review_and_decide_not_detected(self, tmp_path):
        path = tmp_path / "approvals.json"
        gate = ManualApprovalGate(path)
        aid = _request(gate, feature="feature-a")
        reviewed = gate.record(aid)
        # Noncooperating edit between review and decide: advisory locks do not
        # contain it, and no expected-envelope fingerprint exists to detect it.
        stored = json.loads(path.read_text(encoding="utf-8"))
        stored[aid]["payload"]["feature"] = "feature-b"
        _write_gate_file(path, stored)
        gate.decide(aid, APPROVED, decided_by="reviewer-1")
        final = gate.record(aid)
        assert reviewed["payload"]["feature"] == "feature-a"
        assert final["payload"]["feature"] == "feature-b"
        assert final["status"] == APPROVED

    def test_decide_signature_has_no_fingerprint_parameter(self):
        params = set(inspect.signature(ManualApprovalGate.decide).parameters) - {"self"}
        assert params == {"approval_id", "decision", "decided_by"}

    def test_unused_approval_flip_revoke_and_restore_preserved(self, tmp_path):
        # Guard for the documented revoke-unused/restore-unused mechanism that
        # strict one-shot transitions would delete (report section 3.1).
        gate = ManualApprovalGate(tmp_path / "approvals.json")
        aid = _request(gate)
        gate.decide(aid, APPROVED, decided_by="reviewer-1")
        gate.decide(aid, REJECTED, decided_by="reviewer-1")
        gate.decide(aid, APPROVED, decided_by="reviewer-1")
        assert gate.decision(aid) == APPROVED

    def test_consumed_approval_flipped_after_commit_diverges(self, tmp_path):
        gate = ManualApprovalGate(tmp_path / "approvals.json")
        engine = SelfImprovementEngine(module_id=MODULE_ID, module_slug=MODULE_SLUG,
                                       state_dir=tmp_path / "state", gate=gate)
        engine.registry.save_proposal(
            "k1", name="feat", kind="keyword_filter",
            code="def run(items, params=None):\n    return {'items': items}\n",
            test_code="def test_ok():\n    assert True\n", gap_signature="sig")
        proposal = engine.registry.get_proposal("k1")
        approval_id = gate.request(
            module_id=MODULE_ID, module_slug=MODULE_SLUG,
            action_type="self_improvement_activation", summary="x",
            payload={"candidate_key": "k1", "name": "feat", "kind": "keyword_filter",
                     "code_sha256": proposal["code_sha256"], "gap_signature": "sig"})
        engine.registry.set_proposal_approval("k1", approval_id)
        gate.decide(approval_id, APPROVED, decided_by="reviewer-1")
        engine.activate("k1", approval_id=approval_id)

        # Post-commit flip succeeds and rewrites the envelope...
        gate.decide(approval_id, REJECTED, decided_by="reviewer-2")
        record = gate.record(approval_id)
        assert record["status"] == REJECTED
        assert record["decided_by"] == "reviewer-2"
        # ...while the registry effect and consumption record remain committed...
        assert engine.registry.features()["feat"]["active_version"] == 1
        assert len(engine.registry._load()[CONSUMED_KEY]) == 1
        # ...and no decision-event history records the approved state that
        # authorized the commit.
        assert "decision_history" not in record
        with pytest.raises(PermissionError):
            engine.activate("k1", approval_id=approval_id)


# -- PROPOSED semantics: test-local reference implementations ---------------
# These mirror docs/prep/unit-b-decision-envelope-compat-contract.md. They are
# not product code and must not be imported from product modules.


def _canonical_fingerprint(record):
    return hashlib.sha256(
        json.dumps(snapshot_json(record), sort_keys=True, separators=(",", ":"),
                   ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()


def _strict_decide(record, decision, *, expect_fingerprint=None):
    if decision not in (APPROVED, REJECTED):
        raise ValueError("decision must be approved or rejected")
    if expect_fingerprint is not None and \
            _canonical_fingerprint(record) != expect_fingerprint:
        raise PermissionError("stored approval changed since review")
    allowed = {PENDING: {APPROVED, REJECTED}}
    if record["status"] not in allowed or decision not in allowed[record["status"]]:
        raise PermissionError(f"decision transition {record['status']}->{decision} refused")
    return decision


class TestProposedFingerprintContract:
    def test_same_semantic_record_different_raw_bytes_same_fingerprint(self):
        raw_pretty = '{\n  "feature": "x",\n  "order": [1, 2],\n  "n": 3\n}'
        raw_compact = '{"order":[1,2],"n":3,"\\u0066eature":"x"}'
        assert json.loads(raw_pretty) == json.loads(raw_compact)
        assert _canonical_fingerprint(json.loads(raw_pretty)) == \
            _canonical_fingerprint(json.loads(raw_compact))

    def test_integer_and_float_encodings_are_distinct_semantics(self):
        assert _canonical_fingerprint({"t": 1}) != _canonical_fingerprint({"t": 1.0})

    def test_payload_change_changes_fingerprint(self):
        base = {"payload": {"feature": "a"}, "status": PENDING}
        edited = {"payload": {"feature": "b"}, "status": PENDING}
        assert _canonical_fingerprint(base) != _canonical_fingerprint(edited)

    def test_stale_snapshot_fingerprint_refusal(self):
        reviewed = {"payload": {"feature": "a"}, "status": PENDING}
        stored_now = {"payload": {"feature": "b"}, "status": PENDING}
        with pytest.raises(PermissionError, match="changed since review"):
            _strict_decide(stored_now, APPROVED,
                           expect_fingerprint=_canonical_fingerprint(reviewed))

    def test_compat_default_no_fingerprint_allows(self):
        reviewed = {"payload": {"feature": "a"}, "status": PENDING}
        stored_now = {"payload": {"feature": "b"}, "status": PENDING}
        assert _strict_decide(stored_now, APPROVED,
                              expect_fingerprint=None) == APPROVED
        assert _strict_decide(reviewed, APPROVED,
                              expect_fingerprint=_canonical_fingerprint(reviewed)) == APPROVED


class TestProposedTransitionContract:
    @pytest.mark.parametrize("decision", [APPROVED, REJECTED])
    def test_pending_decides_allowed(self, decision):
        assert _strict_decide({"status": PENDING}, decision) == decision

    @pytest.mark.parametrize("status,decision", [
        (APPROVED, REJECTED), (REJECTED, APPROVED),
        (APPROVED, APPROVED), (REJECTED, REJECTED),
    ])
    def test_decided_record_transition_refused(self, status, decision):
        with pytest.raises(PermissionError, match="transition"):
            _strict_decide({"status": status}, decision)

    def test_appended_history_counts_against_j04_budget(self):
        # Proposed history entries live in the same state object, so the J04
        # whole-state snapshot budget (10,000 expanded values) caps them.
        state = {"si-1": {"module_id": MODULE_ID, "module_slug": MODULE_SLUG,
                          "action_type": "self_improvement_rollback", "summary": "x",
                          "payload": {"feature": "f"}, "status": APPROVED,
                          "requested_at": 1.0, "decided_at": 2.0,
                          "decided_by": "reviewer-1", "decision_history": []}}
        snapshot_json(state)  # small state fits the budget today
        entry = {"status": APPROVED, "decided_at": 2.0, "decided_by": "reviewer-1",
                 "envelope_fingerprint": "x" * 64}
        appended = 0
        with pytest.raises(InvalidTelemetryValue):
            while True:
                state["si-1"]["decision_history"].append(dict(entry))
                appended += 1
                snapshot_json(state)
        assert appended > 0  # the budget, not the loop, stopped the growth
