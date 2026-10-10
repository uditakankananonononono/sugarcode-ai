"""UNIT A (PREP-NORUN): approval-ID prefix collision in ManualApprovalGate.request.

AUTHORED, NOT RUN. Synthetic temp files only; no live state, no credentials.

Three groups, kept apart on purpose:

1. CHARACTERIZATION (class names start with TestBase...): assert what the base
   gate ACTUALLY does today when a generated prefix repeats. They detect a real
   overwrite by comparing stored records, never by counting ID lengths. They are
   expected to PASS on the base and to FAIL once a no-overwrite repair lands.
2. DESIRED-REPAIR (TestNoOverwrite...): specify the proposed no-overwrite policy.
   Run against (a) the real base gate, marked xfail(strict) = NOT IMPLEMENTED,
   and (b) ReferenceNoOverwriteGate, a TEST-LOCAL subclass that illustrates the
   proposal. The reference is not product code and changes no existing path.
3. UNCHANGED-BEHAVIOR: cap, durability and legacy-ID behavior that must hold
   for both base and reference.

PROPOSALS (labelled, not decided): MAX_ATTEMPTS = 8, the exception type for
exhaustion, and keeping the "si-" + 12 hex ID shape. A membership check under
the gate lock is what prevents overwrite; retrying with random prefixes does
not make a repeat impossible, it only bounds how often the check has to retry.
"""
import json
import re
import types

import pytest

from sugarcode.self_improve import atomic_file as af
from sugarcode.self_improve import gate as gate_mod
from sugarcode.self_improve.approval_consumption import CONSUMED_KEY, consumption_key
from sugarcode.self_improve.approval_schema import ApprovalSchemaError, validate_record
from sugarcode.self_improve.atomic_file import AtomicDurabilityError
from sugarcode.self_improve.capped_readers import InputLimitExceeded
from sugarcode.self_improve.engine import SelfImprovementEngine
from sugarcode.self_improve.gate import (APPROVED, PENDING, REJECTED, InvalidApprovalState,
                                         ManualApprovalGate)
from sugarcode.self_improve.plans import Candidate, FeaturePlan

P1, P2, P3 = "a" * 12, "b" * 12, "c" * 12
ID1, ID2 = f"si-{P1}", f"si-{P2}"
ACTIVATE = "self_improvement_activation"
NOT_IMPLEMENTED = ("NOT IMPLEMENTED: base ManualApprovalGate.request has no "
                   "collision check; this specifies the PROPOSED repair")


class IdSequenceExhausted(AssertionError):
    """The test's scripted uuid4 prefixes ran out (unexpected extra attempt)."""


class _FakeUUID:
    def __init__(self, prefix):
        assert len(prefix) == 12
        self.hex = prefix + "0" * 20


def patch_ids(monkeypatch, prefixes):
    """Script gate.uuid4 to return the given 12-hex prefixes in order."""
    pending = list(prefixes)
    calls = []

    def fake():
        if not pending:
            raise IdSequenceExhausted(f"uuid4 called more than scripted ({len(calls)} calls)")
        prefix = pending.pop(0)
        calls.append(prefix)
        return _FakeUUID(prefix)

    monkeypatch.setattr(gate_mod, "uuid4", fake)
    return calls


def patch_clock(monkeypatch, start=1000.0):
    """Deterministic gate.time.time(): start, start+1, ... (gate uses only time.time)."""
    state = {"now": start - 1.0}

    def tick():
        state["now"] += 1.0
        return state["now"]

    monkeypatch.setattr(gate_mod, "time", types.SimpleNamespace(time=tick))


class ReferenceNoOverwriteGate(ManualApprovalGate):
    """TEST-LOCAL illustration of the proposed policy, not product code.

    Same record shape and ID format as the base. Under the gate lock, after
    loading the CURRENT file, draw prefixes until one is not already a key (any
    key, whatever its value or status). After MAX_ATTEMPTS draws raise before
    any write.
    """
    MAX_ATTEMPTS = 8  # PROPOSAL

    def request(self, *, module_id, module_slug, action_type, summary, payload):
        with self._lock:
            data = self._load()
            approval_id = None
            for _ in range(self.MAX_ATTEMPTS):
                candidate = f"si-{gate_mod.uuid4().hex[:12]}"
                if candidate not in data:
                    approval_id = candidate
                    break
            if approval_id is None:
                raise InvalidApprovalState("approval id allocation exhausted; state unchanged")
            data[approval_id] = {
                "module_id": module_id, "module_slug": module_slug,
                "action_type": action_type, "summary": summary, "payload": payload,
                "status": APPROVED if self._auto else PENDING,
                "requested_at": gate_mod.time.time(), "decided_at": None,
            }
            try:
                validate_record(data[approval_id], allow_unrecorded_decision=self._auto)
            except ApprovalSchemaError as exc:
                raise InvalidApprovalState("invalid approval record schema") from exc
            try:
                self._save(data)
            except AtomicDurabilityError as exc:
                exc.approval_id = approval_id
                raise
        return approval_id


@pytest.fixture(params=[pytest.param("base", marks=pytest.mark.xfail(strict=True, reason=NOT_IMPLEMENTED)),
                        "reference"])
def desired_gate_cls(request):
    """Desired-repair tests: base is NOT-IMPLEMENTED xfail, reference must pass."""
    return ManualApprovalGate if request.param == "base" else ReferenceNoOverwriteGate


@pytest.fixture(params=["base", "reference"])
def either_gate_cls(request):
    """Unchanged-behavior tests: both must pass, no xfail."""
    return ManualApprovalGate if request.param == "base" else ReferenceNoOverwriteGate


def req(gate, n=1, summary=None, action=ACTIVATE, payload=None):
    return gate.request(module_id=1, module_slug="m", action_type=action,
                        summary=summary or f"request {n}",
                        payload=payload if payload is not None else {"n": n})


def file_state(gate):
    return json.loads(gate._path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# 1. Characterization of the BASE (expected to PASS today)
# --------------------------------------------------------------------------
class TestBaseCollisionCharacterization:
    def test_distinct_prefixes_keep_both_records_control(self, tmp_path, monkeypatch):
        patch_ids(monkeypatch, [P1, P2]); patch_clock(monkeypatch)
        gate = ManualApprovalGate(tmp_path / "gate.json")
        a, b = req(gate, 1), req(gate, 2)
        assert (a, b) == (ID1, ID2)
        assert set(file_state(gate)) == {ID1, ID2}

    def test_id_shape_is_si_plus_12_lowercase_hex(self, tmp_path):
        gate = ManualApprovalGate(tmp_path / "gate.json")
        assert re.fullmatch(r"si-[0-9a-f]{12}", req(gate))

    def test_repeat_prefix_overwrites_pending_record_silently(self, tmp_path, monkeypatch):
        calls = patch_ids(monkeypatch, [P1, P1]); patch_clock(monkeypatch)
        gate = ManualApprovalGate(tmp_path / "gate.json")
        first = req(gate, 1, summary="first")
        before = gate.record(first)
        second = req(gate, 2, summary="second")
        after = gate.record(first)
        assert second == first                      # same ID handed out twice
        assert calls == [P1, P1]                    # no retry, no existence check
        assert list(file_state(gate)) == [first]    # two requests, ONE stored record
        assert before["payload"] == {"n": 1} and before["summary"] == "first"
        assert after["payload"] == {"n": 2} and after["summary"] == "second"
        assert after["requested_at"] > before["requested_at"]

    def test_repeat_prefix_revokes_human_approval(self, tmp_path, monkeypatch):
        patch_ids(monkeypatch, [P1, P1]); patch_clock(monkeypatch)
        gate = ManualApprovalGate(tmp_path / "gate.json")
        first = req(gate, 1)
        gate.decide(first, APPROVED, decided_by="alice")
        before = gate.record(first)
        assert before["status"] == APPROVED and before["decided_by"] == "alice"
        req(gate, 2)
        after = gate.record(first)
        assert after["status"] == PENDING
        assert after["decided_at"] is None and "decided_by" not in after

    def test_repeat_prefix_reopens_rejected_record(self, tmp_path, monkeypatch):
        patch_ids(monkeypatch, [P1, P1]); patch_clock(monkeypatch)
        gate = ManualApprovalGate(tmp_path / "gate.json")
        first = req(gate, 1)
        gate.decide(first, REJECTED, decided_by="alice")
        assert gate.decision(first) == REJECTED
        req(gate, 2)
        assert gate.decision(first) == PENDING

    def test_auto_gate_turns_rejected_record_into_approved_without_decision(self, tmp_path, monkeypatch):
        patch_ids(monkeypatch, [P1, P1]); patch_clock(monkeypatch)
        path = tmp_path / "gate.json"
        manual = ManualApprovalGate(path)
        first = req(manual, 1)
        manual.decide(first, REJECTED, decided_by="alice")
        auto = ManualApprovalGate(path, auto_approve=True)
        req(auto, 2)
        after = manual.record(first)
        assert after["status"] == APPROVED
        assert after["decided_at"] is None and "decided_by" not in after

    @pytest.mark.parametrize("existing", ["garbage", 7, {"status": "approved"}, ["x"], None])
    def test_repeat_prefix_replaces_invalid_existing_entry_masking_corruption(self, tmp_path, monkeypatch, existing):
        patch_ids(monkeypatch, [P1]); patch_clock(monkeypatch)
        gate = ManualApprovalGate(tmp_path / "gate.json")
        gate._path.write_text(json.dumps({ID1: existing}), encoding="utf-8")
        assert req(gate, 1) == ID1
        stored = file_state(gate)[ID1]
        assert stored != existing
        assert stored["payload"] == {"n": 1} and stored["status"] == PENDING


class TestBaseConsumedIdOverwrite:
    """Engine-level: overwriting a CONSUMED approval ID on the base gate."""

    @staticmethod
    def _engine(root, monkeypatch):
        patch_ids(monkeypatch, [P1, P1]); patch_clock(monkeypatch)
        gate = ManualApprovalGate(root / "gate.json")
        engine = SelfImprovementEngine(module_id=1, module_slug="m", state_dir=root, gate=gate)
        cand = Candidate(FeaturePlan("m", "activated", "keyword_filter", "d", "gap", {}),
                         "def run(items,params=None):return items", "")
        engine._candidates[cand.key] = cand
        approval_id = engine.propose(cand.key)
        assert approval_id == ID1
        gate.decide(approval_id, APPROVED, decided_by="alice")
        original = gate.record(approval_id)
        engine.activate(cand.key, approval_id=approval_id)
        consumed = engine.registry._load()[CONSUMED_KEY]
        assert consumption_key(gate._lock.identity, approval_id) in consumed
        return engine, gate, cand.key, approval_id, original

    def test_same_payload_overwrite_loses_gate_history_but_engine_still_refuses(self, tmp_path, monkeypatch):
        engine, gate, key, aid, original = self._engine(tmp_path, monkeypatch)
        # Second request draws the SAME prefix and the SAME payload (binding would pass).
        again = gate.request(module_id=1, module_slug="m", action_type=ACTIVATE,
                             summary=original["summary"], payload=dict(original["payload"]))
        assert again == aid
        reopened = gate.record(aid)
        assert reopened["status"] == PENDING and "decided_by" not in reopened
        assert reopened["requested_at"] > original["requested_at"]
        gate.decide(aid, APPROVED, decided_by="bob")
        # Original decision metadata is gone from the gate (history lost) ...
        assert original["decided_by"] == "alice"
        assert gate.record(aid)["decided_by"] == "bob"
        # ... yet the registry consumption record still blocks a second commit.
        registry_before = engine.registry._path.read_bytes()
        with pytest.raises(PermissionError, match="already consumed"):
            engine.activate(key, approval_id=aid)
        assert engine.registry._path.read_bytes() == registry_before
        assert len(engine.registry._load()[CONSUMED_KEY]) == 1

    def test_different_payload_overwrite_still_refused_by_binding_not_consumption(self, tmp_path, monkeypatch):
        engine, gate, key, aid, original = self._engine(tmp_path, monkeypatch)
        other = dict(original["payload"])
        other["code_sha256"] = "f" * 64
        gate.request(module_id=1, module_slug="m", action_type=ACTIVATE,
                     summary="different", payload=other)
        gate.decide(aid, APPROVED, decided_by="bob")
        assert gate.record(aid)["payload"]["code_sha256"] == "f" * 64   # original payload gone
        registry_before = engine.registry._path.read_bytes()
        with pytest.raises(PermissionError, match="binding mismatch"):
            engine.activate(key, approval_id=aid)
        assert engine.registry._path.read_bytes() == registry_before


# --------------------------------------------------------------------------
# 2. DESIRED-REPAIR: base = xfail(strict, NOT IMPLEMENTED); reference must pass
# --------------------------------------------------------------------------
class TestNoOverwriteDesired:
    def test_pending_record_never_overwritten_and_new_id_differs(self, tmp_path, monkeypatch, desired_gate_cls):
        patch_ids(monkeypatch, [P1, P1, P2]); patch_clock(monkeypatch)
        gate = desired_gate_cls(tmp_path / "gate.json")
        first = req(gate, 1)
        before_record, before_entry = gate.record(first), file_state(gate)[first]
        second = req(gate, 2)
        assert second == ID2 and second != first
        assert gate.record(first) == before_record
        assert file_state(gate)[first] == before_entry
        assert gate.record(second)["payload"] == {"n": 2}
        assert set(file_state(gate)) == {ID1, ID2}

    def test_approved_record_preserved_byte_for_byte(self, tmp_path, monkeypatch, desired_gate_cls):
        patch_ids(monkeypatch, [P1, P1, P2]); patch_clock(monkeypatch)
        gate = desired_gate_cls(tmp_path / "gate.json")
        first = req(gate, 1)
        gate.decide(first, APPROVED, decided_by="alice")
        before = file_state(gate)[first]
        req(gate, 2)
        assert file_state(gate)[first] == before
        assert gate.decision(first) == APPROVED

    def test_rejected_record_stays_rejected(self, tmp_path, monkeypatch, desired_gate_cls):
        patch_ids(monkeypatch, [P1, P1, P2]); patch_clock(monkeypatch)
        gate = desired_gate_cls(tmp_path / "gate.json")
        first = req(gate, 1)
        gate.decide(first, REJECTED, decided_by="alice")
        req(gate, 2)
        assert gate.decision(first) == REJECTED

    def test_auto_gate_cannot_reopen_rejected_record(self, tmp_path, monkeypatch, desired_gate_cls):
        patch_ids(monkeypatch, [P1, P1, P2]); patch_clock(monkeypatch)
        path = tmp_path / "gate.json"
        manual = desired_gate_cls(path)
        first = req(manual, 1)
        manual.decide(first, REJECTED, decided_by="alice")
        auto = desired_gate_cls(path, auto_approve=True)
        new = req(auto, 2)
        assert new == ID2
        assert manual.decision(first) == REJECTED
        assert manual.decision(new) == APPROVED

    @pytest.mark.parametrize("existing", ["garbage", 7, {"status": "approved"}, ["x"], None])
    def test_invalid_existing_entry_is_preserved_not_replaced(self, tmp_path, monkeypatch, desired_gate_cls, existing):
        patch_ids(monkeypatch, [P1, P2]); patch_clock(monkeypatch)
        gate = desired_gate_cls(tmp_path / "gate.json")
        gate._path.write_text(json.dumps({ID1: existing}), encoding="utf-8")
        assert req(gate, 1) == ID2
        assert file_state(gate)[ID1] == existing

    def test_collision_seen_across_gate_objects_via_stored_file(self, tmp_path, monkeypatch, desired_gate_cls):
        patch_ids(monkeypatch, [P1, P1, P2]); patch_clock(monkeypatch)
        path = tmp_path / "gate.json"
        g1, g2 = desired_gate_cls(path), desired_gate_cls(path)
        first = req(g1, 1)
        before = file_state(g1)[first]
        second = req(g2, 2)
        assert second == ID2
        assert file_state(g1)[first] == before

    def test_exhausted_attempts_fail_before_any_write_and_gate_stays_usable(self, tmp_path, monkeypatch, desired_gate_cls):
        # PROPOSAL: cap of 8 draws and InvalidApprovalState on exhaustion.
        cap = getattr(desired_gate_cls, "MAX_ATTEMPTS", 8)
        calls = patch_ids(monkeypatch, [P1] * (1 + cap) + [P2]); patch_clock(monkeypatch)
        gate = desired_gate_cls(tmp_path / "gate.json")
        first = req(gate, 1)
        before_bytes = gate._path.read_bytes()
        with pytest.raises(InvalidApprovalState, match="state unchanged"):
            req(gate, 2)
        assert gate._path.read_bytes() == before_bytes
        assert len(calls) == 1 + cap          # finite: no unbounded loop
        assert req(gate, 3) == ID2             # still usable afterwards
        assert gate.record(first)["payload"] == {"n": 1}

    def test_durability_error_reports_the_retried_id_not_the_colliding_one(self, tmp_path, monkeypatch, desired_gate_cls):
        patch_ids(monkeypatch, [P1, P1, P2]); patch_clock(monkeypatch)
        gate = desired_gate_cls(tmp_path / "gate.json")
        first = req(gate, 1)
        before = file_state(gate)[first]

        def fail(_directory):
            raise OSError("directory sync failed")
        monkeypatch.setattr(af, "_fsync_dir", fail)
        with pytest.raises(AtomicDurabilityError) as caught:
            req(gate, 2)
        assert caught.value.approval_id == ID2
        state = file_state(gate)
        assert state[first] == before and ID2 in state     # new state replaced, old intact

    def test_consumed_id_history_survives_a_colliding_request(self, tmp_path, monkeypatch, desired_gate_cls):
        patch_ids(monkeypatch, [P1, P1, P2]); patch_clock(monkeypatch)
        gate = desired_gate_cls(tmp_path / "gate.json")
        engine = SelfImprovementEngine(module_id=1, module_slug="m", state_dir=tmp_path, gate=gate)
        cand = Candidate(FeaturePlan("m", "activated", "keyword_filter", "d", "gap", {}),
                         "def run(items,params=None):return items", "")
        engine._candidates[cand.key] = cand
        aid = engine.propose(cand.key)
        gate.decide(aid, APPROVED, decided_by="alice")
        original = file_state(gate)[aid]
        engine.activate(cand.key, approval_id=aid)
        again = gate.request(module_id=1, module_slug="m", action_type=ACTIVATE,
                             summary="again", payload=dict(original["payload"]))
        assert again == ID2
        assert file_state(gate)[aid] == original                 # decided_by alice kept
        assert len(engine.registry._load()[CONSUMED_KEY]) == 1


# --------------------------------------------------------------------------
# 3. UNCHANGED BEHAVIOR for base and reference (no xfail)
# --------------------------------------------------------------------------
class TestUnchangedBehavior:
    def test_id_format_unchanged(self, tmp_path, either_gate_cls):
        assert re.fullmatch(r"si-[0-9a-f]{12}", req(either_gate_cls(tmp_path / "gate.json")))

    def test_finite_cap_unchanged_and_refusal_leaves_state_untouched(self, tmp_path, monkeypatch, either_gate_cls):
        patch_ids(monkeypatch, [P1, P2]); patch_clock(monkeypatch)
        gate = either_gate_cls(tmp_path / "gate.json")
        req(gate, 1)
        before = gate._path.read_bytes()
        monkeypatch.setattr(gate_mod, "APPROVAL_FILE_BYTES", len(before) + 1)
        with pytest.raises(InputLimitExceeded):
            req(gate, 2)
        assert gate._path.read_bytes() == before
        assert ID2 not in file_state(gate)

    def test_postreplace_durability_error_carries_new_id(self, tmp_path, monkeypatch, either_gate_cls):
        patch_ids(monkeypatch, [P1]); patch_clock(monkeypatch)
        gate = either_gate_cls(tmp_path / "gate.json")

        def fail(_directory):
            raise OSError("directory sync failed")
        monkeypatch.setattr(af, "_fsync_dir", fail)
        with pytest.raises(AtomicDurabilityError) as caught:
            req(gate, 1)
        assert caught.value.approval_id == ID1
        assert ID1 in file_state(gate)          # replace landed; blind retry is not safe

    def test_prewrite_failure_leaves_file_unchanged(self, tmp_path, monkeypatch, either_gate_cls):
        patch_ids(monkeypatch, [P1]); patch_clock(monkeypatch)
        gate = either_gate_cls(tmp_path / "gate.json")
        before = gate._path.read_bytes()
        with pytest.raises(InvalidApprovalState, match="state unchanged"):
            gate.request(module_id=1, module_slug="m", action_type=ACTIVATE,
                         summary="x", payload={"bad": float("nan")})
        assert gate._path.read_bytes() == before

    def test_legacy_non_si_ids_and_minimal_records_untouched(self, tmp_path, monkeypatch, either_gate_cls):
        patch_ids(monkeypatch, [P1]); patch_clock(monkeypatch)
        gate = either_gate_cls(tmp_path / "gate.json")
        legacy = {"legacy-1": {"status": "approved"}, "seed": {"status": "pending"}}
        gate._path.write_text(json.dumps(legacy), encoding="utf-8")
        new = req(gate, 1)
        state = file_state(gate)
        assert new == ID1
        assert state["legacy-1"] == legacy["legacy-1"] and state["seed"] == legacy["seed"]
        assert gate.decision("legacy-1") == APPROVED
        gate.decide("seed", REJECTED, decided_by="alice")
        assert gate.decision("seed") == REJECTED
