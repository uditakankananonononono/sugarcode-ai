"""SC-A01 rollback approval target binding - AUTHORED, NOT RUN.

Authored under additions-only/no-test-run prep constraints. No case here
has been executed by the builder; execution and the independent verdict
belong to the integration owner.

TestEngineBindingValidator covers the pure helper and passes standalone.
TestEngineWiringCanaries covers the engine.rollback() repair itself: those
cases FAIL on the pre-wiring base (engine.rollback accepts any approved
id) and that failure is the intended canary proving they detect the
defect; they pass only after the integration wiring documented in
docs/approval-rollback-binding.md lands.
"""
import pytest

from sugarcode.self_improve.approval_binding import (
    ACTIVATION_ACTION,
    ROLLBACK_ACTION,
    ApprovalBindingError,
    ApprovalBindingMismatch,
    BindingReport,
    InvalidApprovalRecord,
    rollback_target,
    validate_rollback_binding,
    validate_rollback_request,
)
from sugarcode.self_improve.engine import SelfImprovementEngine
from sugarcode.self_improve.gate import APPROVED, ManualApprovalGate

MODULE_ID = 3
MODULE_SLUG = "grants"
FEATURE = "deadline_filter"


def rollback_record(**overrides):
    record = {
        "module_id": MODULE_ID,
        "module_slug": MODULE_SLUG,
        "action_type": ROLLBACK_ACTION,
        "summary": "Roll back self-built feature deadline_filter on grants",
        "payload": {"feature": FEATURE},
        "status": "approved",
        "requested_at": 1_700_000_000.0,
        "decided_at": 1_700_000_100.0,
        "decided_by": "human",
    }
    for key, value in overrides.items():
        if key == "payload":
            record["payload"] = value
        else:
            record[key] = value
    return record


class TestEngineBindingValidator:
    """Pure validator cases; no engine or gate wiring required."""

    def test_valid_rollback_record_binds(self):
        report = validate_rollback_binding(
            rollback_record(), module_id=MODULE_ID, module_slug=MODULE_SLUG,
            feature_name=FEATURE)
        assert report == BindingReport(module_id=MODULE_ID, module_slug=MODULE_SLUG,
                                       action_type=ROLLBACK_ACTION, feature=FEATURE,
                                       version_bound=False)

    def test_activation_approval_cannot_roll_back(self):
        record = rollback_record(action_type=ACTIVATION_ACTION,
                                 payload={"candidate_key": "k1", "name": FEATURE})
        with pytest.raises(ApprovalBindingMismatch, match="action"):
            validate_rollback_binding(record, module_id=MODULE_ID,
                                      module_slug=MODULE_SLUG, feature_name=FEATURE)

    @pytest.mark.parametrize("other", ["other_feature", FEATURE + "_v2", "", FEATURE.upper()])
    def test_approval_for_different_feature_cannot_roll_back_target(self, other):
        record = rollback_record(payload={"feature": other})
        with pytest.raises(ApprovalBindingMismatch, match="feature"):
            validate_rollback_binding(record, module_id=MODULE_ID,
                                      module_slug=MODULE_SLUG, feature_name=FEATURE)

    @pytest.mark.parametrize("field,value", [("module_id", MODULE_ID + 1),
                                             ("module_slug", "other-module")])
    def test_approval_for_different_module_cannot_roll_back_target(self, field, value):
        record = rollback_record(**{field: value})
        with pytest.raises(ApprovalBindingMismatch, match="module"):
            validate_rollback_binding(record, module_id=MODULE_ID,
                                      module_slug=MODULE_SLUG, feature_name=FEATURE)

    @pytest.mark.parametrize("missing", ["module_id", "module_slug", "action_type", "payload"])
    def test_missing_required_field_is_invalid(self, missing):
        record = rollback_record()
        del record[missing]
        with pytest.raises(InvalidApprovalRecord, match="missing"):
            validate_rollback_binding(record, module_id=MODULE_ID,
                                      module_slug=MODULE_SLUG, feature_name=FEATURE)

    @pytest.mark.parametrize("field,value", [
        ("module_id", True),            # bool is not a module identity
        ("module_id", "3"),
        ("module_id", 3.0),
        ("module_slug", 3),
        ("module_slug", None),
        ("action_type", None),
    ])
    def test_field_type_strictness(self, field, value):
        record = rollback_record(**{field: value})
        with pytest.raises(InvalidApprovalRecord):
            validate_rollback_binding(record, module_id=MODULE_ID,
                                      module_slug=MODULE_SLUG, feature_name=FEATURE)

    @pytest.mark.parametrize("bad", [None, 1, ["x"], {"x": 1}, True])
    def test_payload_must_be_mapping_or_feature_string(self, bad):
        record = rollback_record(payload=bad)
        with pytest.raises(InvalidApprovalRecord):
            validate_rollback_binding(record, module_id=MODULE_ID,
                                      module_slug=MODULE_SLUG, feature_name=FEATURE)

    @pytest.mark.parametrize("bad", [None, 1, ["x"], True])
    def test_rollback_payload_feature_must_be_string(self, bad):
        record = rollback_record(payload={"feature": bad})
        with pytest.raises(InvalidApprovalRecord, match="feature"):
            validate_rollback_binding(record, module_id=MODULE_ID,
                                      module_slug=MODULE_SLUG, feature_name=FEATURE)

    def test_non_mapping_record_is_invalid(self):
        for bad in (None, [], "approval", 42):
            with pytest.raises(InvalidApprovalRecord):
                validate_rollback_binding(bad, module_id=MODULE_ID,
                                          module_slug=MODULE_SLUG, feature_name=FEATURE)

    def test_unknown_extra_keys_are_tolerated(self):
        record = rollback_record(future_field={"nested": [1, 2]})
        record["payload"]["extra"] = "ignored"
        report = validate_rollback_binding(record, module_id=MODULE_ID,
                                           module_slug=MODULE_SLUG, feature_name=FEATURE)
        assert report.feature == FEATURE

    def test_status_is_not_inspected_by_binding(self):
        # Decision status is the gate's check and J05's schema, not binding's.
        # Binding must accept a well-formed record regardless of status value so
        # the engine's decision check remains the single status authority.
        for status in ("approved", "pending", "rejected"):
            report = validate_rollback_binding(
                rollback_record(status=status), module_id=MODULE_ID,
                module_slug=MODULE_SLUG, feature_name=FEATURE)
            assert report.feature == FEATURE

    def test_version_pin_matching_binds(self):
        record = rollback_record(payload={"feature": FEATURE,
                                          "active_version_at_request": 2})
        report = validate_rollback_binding(record, module_id=MODULE_ID,
                                           module_slug=MODULE_SLUG, feature_name=FEATURE,
                                           current_active_version=2)
        assert report.version_bound is True

    def test_version_pin_mismatch_refuses(self):
        # Feature moved to v3 after the human approved rolling back v2.
        record = rollback_record(payload={"feature": FEATURE,
                                          "active_version_at_request": 2})
        with pytest.raises(ApprovalBindingMismatch, match="version"):
            validate_rollback_binding(record, module_id=MODULE_ID,
                                      module_slug=MODULE_SLUG, feature_name=FEATURE,
                                      current_active_version=3)

    def test_version_pin_requires_caller_version(self):
        record = rollback_record(payload={"feature": FEATURE,
                                          "active_version_at_request": 2})
        with pytest.raises(ApprovalBindingError, match="current_active_version"):
            validate_rollback_binding(record, module_id=MODULE_ID,
                                      module_slug=MODULE_SLUG, feature_name=FEATURE)

    def test_version_pin_null_binds_to_inactive_at_request(self):
        record = rollback_record(payload={"feature": FEATURE,
                                          "active_version_at_request": None})
        report = validate_rollback_binding(record, module_id=MODULE_ID,
                                           module_slug=MODULE_SLUG, feature_name=FEATURE,
                                           current_active_version=None)
        assert report.version_bound is False

    @pytest.mark.parametrize("bad", ["2", 2.0, True])
    def test_version_pin_type_strictness(self, bad):
        record = rollback_record(payload={"feature": FEATURE,
                                          "active_version_at_request": bad})
        with pytest.raises(InvalidApprovalRecord, match="active_version_at_request"):
            validate_rollback_binding(record, module_id=MODULE_ID,
                                      module_slug=MODULE_SLUG, feature_name=FEATURE,
                                      current_active_version=2)

    def test_unpinned_record_reports_weaker_binding(self):
        # All records written by the current engine pin no version; the caller
        # sees version_bound=False and can apply its own policy.
        report = validate_rollback_binding(
            rollback_record(), module_id=MODULE_ID, module_slug=MODULE_SLUG,
            feature_name=FEATURE, current_active_version=2)
        assert report.version_bound is False

    def test_rollback_target_shape_check_only(self):
        target = rollback_target(rollback_record())
        assert target.feature == FEATURE and target.action_type == ROLLBACK_ACTION

    @pytest.mark.parametrize("kwargs", [
        {"module_id": "3"}, {"module_id": True}, {"module_slug": 3},
        {"feature_name": None}, {"current_active_version": "2"},
    ])
    def test_caller_argument_type_errors(self, kwargs):
        call = dict(module_id=MODULE_ID, module_slug=MODULE_SLUG, feature_name=FEATURE)
        call.update(kwargs)
        with pytest.raises(TypeError):
            validate_rollback_binding(rollback_record(), **call)


class DictRecordSource:
    """Minimal stand-in for the pending SC-J05 record read API."""

    def __init__(self, records):
        self._records = dict(records)

    def record(self, approval_id):
        if approval_id not in self._records:
            raise KeyError(f"unknown approval {approval_id!r}")
        return self._records[approval_id]


class TestRecordSourcePath:
    def test_valid_fetch_and_bind(self):
        source = DictRecordSource({"si-abc": rollback_record()})
        report = validate_rollback_request(source, "si-abc", module_id=MODULE_ID,
                                           module_slug=MODULE_SLUG, feature_name=FEATURE)
        assert report.feature == FEATURE

    def test_unknown_approval_id_propagates_keyerror(self):
        source = DictRecordSource({})
        with pytest.raises(KeyError):
            validate_rollback_request(source, "si-missing", module_id=MODULE_ID,
                                      module_slug=MODULE_SLUG, feature_name=FEATURE)

    def test_mismatched_fetched_record_refuses(self):
        source = DictRecordSource(
            {"si-abc": rollback_record(payload={"feature": "other"})})
        with pytest.raises(ApprovalBindingMismatch):
            validate_rollback_request(source, "si-abc", module_id=MODULE_ID,
                                      module_slug=MODULE_SLUG, feature_name=FEATURE)

    def test_approval_id_type_checked(self):
        with pytest.raises(TypeError):
            validate_rollback_request(DictRecordSource({}), None, module_id=MODULE_ID,
                                      module_slug=MODULE_SLUG, feature_name=FEATURE)


def _engine_with_active_feature(tmp_path, *, module_id=MODULE_ID,
                                module_slug=MODULE_SLUG, feature=FEATURE,
                                gate=None):
    gate = gate or ManualApprovalGate(tmp_path / "approvals.json", auto_approve=True)
    engine = SelfImprovementEngine(module_id=module_id, module_slug=module_slug,
                                   state_dir=tmp_path, gate=gate)
    engine.registry.save_proposal(
        "k1", name=feature, kind="keyword_filter",
        code="def run(items, params=None):\n    return {'items': items}\n",
        test_code="def test_ok():\n    assert True\n",
        gap_signature="sig")
    engine.registry.activate("k1", approval_id="seed-activation")
    return engine, gate


class TestEngineWiringCanaries:
    """Engine-level done criteria for SC-A01. These exercise real state
    transitions. On the pre-wiring base the mismatch cases FAIL because
    engine.rollback accepts any approved id; that failure is the canary
    proving detection. They pass only after the documented wiring lands.
    """

    def test_activation_approval_cannot_roll_back_feature(self, tmp_path):
        engine, gate = _engine_with_active_feature(tmp_path)
        activation_id = gate.request(
            module_id=MODULE_ID, module_slug=MODULE_SLUG,
            action_type=ACTIVATION_ACTION, summary="activate",
            payload={"candidate_key": "k1", "name": FEATURE})
        gate.decide(activation_id, APPROVED)
        with pytest.raises(PermissionError):
            engine.rollback(FEATURE, approval_id=activation_id)
        assert engine.registry.features()[FEATURE]["active_version"] == 1

    def test_rollback_approval_for_other_feature_cannot_roll_back_target(self, tmp_path):
        engine, gate = _engine_with_active_feature(tmp_path)
        other_id = gate.request(
            module_id=MODULE_ID, module_slug=MODULE_SLUG,
            action_type=ROLLBACK_ACTION, summary="roll back other",
            payload={"feature": "other_feature"})
        gate.decide(other_id, APPROVED)
        with pytest.raises(PermissionError):
            engine.rollback(FEATURE, approval_id=other_id)
        assert engine.registry.features()[FEATURE]["active_version"] == 1

    def test_rollback_approval_from_other_module_cannot_roll_back(self, tmp_path):
        gate = ManualApprovalGate(tmp_path / "approvals.json", auto_approve=True)
        engine, _ = _engine_with_active_feature(tmp_path / "a", gate=gate)
        other_engine, _ = _engine_with_active_feature(tmp_path / "b", module_id=MODULE_ID+1,
                                                      module_slug="other-module", gate=gate)
        foreign_id = other_engine.request_rollback(FEATURE)
        gate.decide(foreign_id, APPROVED)
        with pytest.raises(PermissionError):
            engine.rollback(FEATURE, approval_id=foreign_id)
        assert engine.registry.features()[FEATURE]["active_version"] == 1

    def test_correct_rollback_request_still_rolls_back(self, tmp_path):
        engine, gate = _engine_with_active_feature(tmp_path)
        approval_id = engine.request_rollback(FEATURE)
        gate.decide(approval_id, APPROVED)
        outcome = engine.rollback(FEATURE, approval_id=approval_id)
        assert outcome["rolled_back_from"] == 1
        assert outcome["active_version"] is None

    def test_pending_rollback_approval_cannot_roll_back(self, tmp_path):
        gate = ManualApprovalGate(tmp_path / "approvals.json", auto_approve=False)
        engine, _ = _engine_with_active_feature(tmp_path, gate=gate)
        approval_id = engine.request_rollback(FEATURE)
        with pytest.raises(PermissionError):
            engine.rollback(FEATURE, approval_id=approval_id)
        assert engine.registry.features()[FEATURE]["active_version"] == 1

    def test_rollback_of_missing_feature_raises_keyerror(self, tmp_path):
        engine, gate = _engine_with_active_feature(tmp_path)
        with pytest.raises(KeyError):
            engine.request_rollback("no_such_feature")

    def test_rollback_of_inactive_feature_raises_keyerror(self, tmp_path):
        engine, gate = _engine_with_active_feature(tmp_path)
        first = engine.request_rollback(FEATURE)
        gate.decide(first, APPROVED)
        engine.rollback(FEATURE, approval_id=first)
        with pytest.raises(KeyError):
            engine.request_rollback(FEATURE)
