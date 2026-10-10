"""Bad caller values cannot poison or truncate approval state on serialization."""
import json
from decimal import Decimal

import pytest

from sugarcode.self_improve.gate import APPROVED, PENDING, InvalidApprovalState, ManualApprovalGate


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf"), Decimal(1), {1: "x"}, object()])
def test_invalid_request_payload_keeps_gate_usable(tmp_path, bad):
    path = tmp_path / "gate.json"
    gate = ManualApprovalGate(path)
    before = path.read_bytes()
    with pytest.raises(InvalidApprovalState, match="state unchanged"):
        gate.request(module_id=1, module_slug="m", action_type="activate",
                     summary="x", payload={"bad": bad})
    assert path.read_bytes() == before
    good = gate.request(module_id=1, module_slug="m", action_type="activate",
                        summary="x", payload={"valid": 1})
    assert gate.decision(good) == PENDING


def test_cyclic_and_hostile_payload_never_converted(tmp_path):
    gate = ManualApprovalGate(tmp_path / "gate.json")
    before = gate._path.read_bytes()
    cycle = []; cycle.append(cycle)
    class Hostile:
        def __str__(self):
            pytest.fail("str invoked")
        def __repr__(self):
            pytest.fail("repr invoked")
        def __deepcopy__(self, memo):
            pytest.fail("deepcopy invoked")
    for value in (cycle, Hostile()):
        with pytest.raises(InvalidApprovalState):
            gate.request(module_id=1, module_slug="m", action_type="activate",
                         summary="x", payload={"value": value})
        assert gate._path.read_bytes() == before


@pytest.mark.parametrize("failure", [ValueError, TypeError, RecursionError])
def test_serialization_failure_before_write(tmp_path, monkeypatch, failure):
    gate = ManualApprovalGate(tmp_path / "gate.json")
    before = gate._path.read_bytes()
    def bad(*args, **kwargs):
        raise failure("encoder failure")
    monkeypatch.setattr(json, "dumps", bad)
    with pytest.raises(InvalidApprovalState) as caught:
        gate._save({})
    assert type(caught.value.__cause__) is failure
    assert gate._path.read_bytes() == before


def test_invalid_decided_by_does_not_change_pending_request(tmp_path):
    gate = ManualApprovalGate(tmp_path / "gate.json")
    approval = gate.request(module_id=1, module_slug="m", action_type="activate", summary="x", payload={})
    before = gate._path.read_bytes()
    with pytest.raises(InvalidApprovalState):
        gate.decide(approval, APPROVED, decided_by=float("nan"))
    assert gate._path.read_bytes() == before
    assert gate.decision(approval) == PENDING
    gate.decide(approval, APPROVED)
    assert gate.decision(approval) == APPROVED


def test_payload_detached_tuples_and_string_nan_preserved(tmp_path):
    gate = ManualApprovalGate(tmp_path / "gate.json")
    payload = {"x": [1, (2, "NaN")]}
    approval = gate.request(module_id=1, module_slug="m", action_type="activate", summary="x", payload=payload)
    payload["x"].append("late")
    assert gate._load()[approval]["payload"] == {"x": [1, [2, "NaN"]]}


def test_whole_state_depth_and_value_budget_fail_without_write(tmp_path):
    gate = ManualApprovalGate(tmp_path / "gate.json")
    before = gate._path.read_bytes()
    deep = []
    for _ in range(66):
        deep = [deep]
    for value in (deep, [0] * 10000):
        with pytest.raises(InvalidApprovalState):
            gate._save({"value": value})
        assert gate._path.read_bytes() == before


def test_real_oversized_integer_serialization_is_typed(tmp_path):
    import sys
    if not hasattr(sys, "set_int_max_str_digits"):
        pytest.skip("no configurable integer string limit")
    old = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(640)
        gate = ManualApprovalGate(tmp_path / "gate.json")
        before = gate._path.read_bytes()
        with pytest.raises(InvalidApprovalState):
            gate._save({"huge": 10**700})
        assert gate._path.read_bytes() == before
    finally:
        sys.set_int_max_str_digits(old)
