"""AUTHORED, NOT RUN. Approval record schema/binding helper (SC-J05 prep)."""
import copy
import math

import pytest

from sugarcode.self_improve.approval_schema import (
    ACTIVATION_ACTION, ROLLBACK_ACTION, ActivationExpectation, ApprovalSchemaError,
    RollbackExpectation, check_binding, require_approved, validate_payload, validate_record)

SHA = "a" * 64


def act_payload():
    return {"candidate_key": "ck1", "name": "feat", "kind": "rule", "code_sha256": SHA,
            "gap_signature": "gap1"}


def record(action=ACTIVATION_ACTION, payload=None, status="approved", **over):
    base = {"module_id": 7, "module_slug": "mod", "action_type": action,
            "summary": "s", "payload": payload if payload is not None else act_payload(),
            "status": status, "requested_at": 1.5,
            "decided_at": None if status == "pending" else 2.5}
    if status != "pending":
        base["decided_by"] = "human"
    base.update(over)
    return base


def act_exp(**over):
    d = dict(module_id=7, module_slug="mod", candidate_key="ck1", name="feat",
             kind="rule", code_sha256=SHA, gap_signature="gap1")
    d.update(over)
    return ActivationExpectation(**d)


def rb_exp(**over):
    d = dict(module_id=7, module_slug="mod", feature="feat")
    d.update(over)
    return RollbackExpectation(**d)


def rb_record(**over):
    return record(ROLLBACK_ACTION, {"feature": "feat"}, **over)


def err(code):
    return pytest.raises(ApprovalSchemaError, match=code)


def test_valid_activation_roundtrip_approved():
    require_approved(record(), act_exp())


def test_valid_rollback_roundtrip_approved():
    require_approved(rb_record(), rb_exp())


def test_pending_and_rejected_are_valid_but_not_approved():
    assert check_binding(record(status="pending"), act_exp()) == "pending"
    assert check_binding(record(status="rejected"), act_exp()) == "rejected"
    for status in ("pending", "rejected"):
        with pytest.raises(PermissionError):
            require_approved(record(status=status), act_exp())
        with pytest.raises(PermissionError):
            require_approved(rb_record(status=status), rb_exp())


@pytest.mark.parametrize("bad", [None, [], "approved", 1, ()])
def test_non_object_record_refused(bad):
    with err("record_not_object"):
        validate_record(bad)


@pytest.mark.parametrize("field", ["module_id", "module_slug", "action_type", "summary",
                                   "payload", "status", "requested_at", "decided_at"])
def test_missing_required_field_refused(field):
    r = record()
    del r[field]
    with err("record_missing_field"):
        validate_record(r)


def test_unexpected_field_refused():
    with err("record_unexpected_field"):
        validate_record(record(extra=1))


def test_non_string_key_refused():
    r = record()
    r[1] = "x"
    with err("record_key_type"):
        validate_record(r)


@pytest.mark.parametrize("field,value,code", [
    ("module_id", True, "module_id_type"), ("module_id", "7", "module_id_type"),
    ("module_id", 7.0, "module_id_type"),
    ("module_slug", "", "module_slug_type"), ("module_slug", 5, "module_slug_type"),
    ("action_type", "", "action_type_type"), ("action_type", None, "action_type_type"),
    ("summary", None, "summary_type"), ("payload", [], "payload_type"),
    ("payload", None, "payload_type"),
    ("status", "APPROVED", "status_invalid"), ("status", "", "status_invalid"),
    ("status", None, "status_invalid"), ("status", ["approved"], "status_invalid"),
    ("status", True, "status_invalid"),
    ("requested_at", "1", "requested_at_type"), ("requested_at", True, "requested_at_type"),
    ("requested_at", math.nan, "requested_at_type"),
    ("requested_at", math.inf, "requested_at_type"),
    ("decided_at", "2", "decided_at_type"), ("decided_at", math.nan, "decided_at_type"),
    ("decided_by", "", "decided_by_type"), ("decided_by", 3, "decided_by_type"),
])
def test_field_type_refused(field, value, code):
    with err(code):
        validate_record(record(**{field: value}))


def test_str_subclass_status_refused():
    class S(str):
        pass
    with err("status_invalid"):
        validate_record(record(status=S("approved")))


def test_dict_subclass_record_and_payload_refused():
    class D(dict):
        pass
    with err("record_not_object"):
        validate_record(D(record()))
    with err("payload_type"):
        validate_record(record(payload=D(act_payload())))


def test_pending_with_decision_refused():
    with err("pending_has_decision"):
        validate_record(record(status="pending", decided_at=3.0))
    with err("pending_has_decision"):
        validate_record(record(status="pending", decided_by="human"))


def test_decided_without_decision_metadata_refused_by_default():
    r = record()
    r["decided_at"] = None
    del r["decided_by"]
    with err("decision_not_recorded"):
        validate_record(r)


def test_partial_decision_metadata_refused_even_when_unrecorded_allowed():
    r = record()
    del r["decided_by"]
    with err("decision_not_recorded"):
        validate_record(r, allow_unrecorded_decision=True)
    r = record(decided_at=None)
    with err("decision_not_recorded"):
        validate_record(r, allow_unrecorded_decision=True)


def test_auto_approve_shape_accepted_only_with_flag():
    r = record()
    r["decided_at"] = None
    del r["decided_by"]
    assert validate_record(r, allow_unrecorded_decision=True) is r
    require_approved(r, act_exp(), allow_unrecorded_decision=True)
    with pytest.raises(ApprovalSchemaError):
        require_approved(r, act_exp())


def test_validate_does_not_mutate_input():
    r = record()
    before = copy.deepcopy(r)
    check_binding(r, act_exp())
    assert r == before


def test_wrong_action_for_operation():
    with err("action_mismatch"):
        require_approved(rb_record(), act_exp())
    with err("action_mismatch"):
        require_approved(record(), rb_exp())
    with err("action_mismatch"):
        require_approved(record(action="other_action"), act_exp())


def test_unknown_action_payload_refused():
    with err("action_unknown"):
        validate_payload("other_action", {})


def test_module_id_and_slug_mismatch():
    with err("module_id_mismatch"):
        require_approved(record(module_id=8), act_exp())
    with err("module_slug_mismatch"):
        require_approved(record(module_slug="other"), act_exp())
    with err("module_id_mismatch"):
        require_approved(rb_record(module_id=8), rb_exp())
    with err("module_slug_mismatch"):
        require_approved(rb_record(module_slug="other"), rb_exp())


@pytest.mark.parametrize("field", ["candidate_key", "name", "kind", "gap_signature"])
def test_activation_identity_mismatch(field):
    with err(f"{field}_mismatch"):
        require_approved(record(), act_exp(**{field: "different"}))


def test_activation_hash_mismatch():
    with err("code_sha256_mismatch"):
        require_approved(record(), act_exp(code_sha256="b" * 64))


def test_rollback_feature_mismatch():
    with err("feature_mismatch"):
        require_approved(rb_record(), rb_exp(feature="other"))


@pytest.mark.parametrize("drop", sorted(["candidate_key", "name", "kind", "code_sha256", "gap_signature"]))
def test_activation_payload_missing_key(drop):
    p = act_payload()
    del p[drop]
    with err("payload_keys"):
        require_approved(record(payload=p), act_exp())


def test_activation_payload_extra_key_and_rollback_shapes():
    p = act_payload()
    p["extra"] = "x"
    with err("payload_keys"):
        require_approved(record(payload=p), act_exp())
    with err("payload_keys"):
        require_approved(rb_record(payload={}), rb_exp())
    with err("payload_keys"):
        require_approved(rb_record(payload={"feature": "feat", "x": "y"}), rb_exp())
    with err("payload_keys"):
        require_approved(rb_record(payload=act_payload()), rb_exp())


@pytest.mark.parametrize("value", [None, 1, "", ["x"], {"a": 1}])
def test_payload_field_wrong_type_or_empty(value):
    p = act_payload()
    p["name"] = value
    with err("payload_field_type"):
        require_approved(record(payload=p), act_exp())
    with err("payload_field_type"):
        require_approved(rb_record(payload={"feature": value}), rb_exp())


@pytest.mark.parametrize("sha", ["A" * 64, "a" * 63, "a" * 65, "g" * 64, " " + "a" * 63,
                                 "a" * 64 + "\n"])
def test_bad_hash_format_refused(sha):
    p = act_payload()
    p["code_sha256"] = sha
    with err("code_sha256_format"):
        require_approved(record(payload=p), act_exp(code_sha256=sha))


def test_payload_non_string_key_refused():
    p = act_payload()
    p[1] = "x"
    with err("payload_key_type"):
        validate_payload(ACTIVATION_ACTION, p)


def test_bad_expectation_type_refused():
    with err("expectation_type"):
        check_binding(record(), {"module_id": 7})


def test_activation_record_cannot_satisfy_rollback_of_same_name():
    # Same feature name and module, but an activation approval.
    with err("action_mismatch"):
        require_approved(record(payload={**act_payload(), "name": "feat"}), rb_exp(feature="feat"))


def test_error_message_has_no_payload_values():
    p = act_payload()
    p["name"] = "SECRET-NAME"
    with pytest.raises(ApprovalSchemaError) as info:
        require_approved(record(payload=p), act_exp())
    assert "SECRET-NAME" not in str(info.value)
    assert info.value.code == "name_mismatch"
