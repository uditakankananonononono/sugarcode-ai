"""Stored gate JSON refuses ambiguity without rewriting or granting decisions."""
import pytest

from sugarcode.self_improve.gate import APPROVED, PENDING, ManualApprovalGate


BAD_STATES = [
    '{"id":{"status":"rejected","status":"approved"}}',
    '{"id":{"status":"pending"},"id":{"status":"approved"}}',
    r'{"id":{"status":"pending","\u0073tatus":"approved"}}',
    '{"id":{"status":"pending","payload":[{"x":1,"x":2}]}}',
    '{"id":{"status":"pending","payload":{"x":NaN}}}',
    '{"id":{"status":"pending","payload":{"x":Infinity}}}',
    '{"id":{"status":"pending","payload":{"x":-Infinity}}}',
    '{"id":{"status":"pending","payload":{"x":1e999}}}',
    '[]', 'null', '"approved"', '{bad',
]


@pytest.mark.parametrize("state", BAD_STATES)
@pytest.mark.parametrize("operation", ["decision", "request", "decide"])
def test_bad_state_refuses_every_gate_operation_without_rewrite(tmp_path, state, operation):
    from sugarcode.self_improve.gate import InvalidApprovalState
    path = tmp_path / "approvals.json"
    path.write_text(state)
    gate = ManualApprovalGate(path)
    before = path.read_bytes()
    with pytest.raises(InvalidApprovalState, match="repair required"):
        if operation == "decision":
            gate.decision("id")
        elif operation == "decide":
            gate.decide("id", APPROVED)
        else:
            gate.request(module_id=1, module_slug="m", action_type="activate",
                         summary="candidate", payload={})
    assert path.read_bytes() == before


def test_valid_unicode_and_same_keys_in_separate_objects(tmp_path):
    path = tmp_path / "approvals.json"
    path.write_text('{"a":{"status":"pending","payload":{"x":1}},"b":{"status":"approved","payload":{"x":2}}}')
    gate = ManualApprovalGate(path)
    assert gate.decision("a") == PENDING
    assert gate.decision("b") == APPROVED
    gate.decide("a", APPROVED)
    assert gate.decision("a") == APPROVED


def test_new_gate_normal_request_and_decision(tmp_path):
    gate = ManualApprovalGate(tmp_path / "new.json")
    approval = gate.request(module_id=1, module_slug="m", action_type="activate",
                            summary="candidate", payload={"finite": 1e100})
    assert gate.decision(approval) == PENDING
    gate.decide(approval, APPROVED)
    assert gate.decision(approval) == APPROVED
