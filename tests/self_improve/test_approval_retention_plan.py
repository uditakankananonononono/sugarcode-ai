"""SC-H01 authored-not-run pure-helper and protocol-model canaries."""
from dataclasses import replace
import json

import pytest

from sugarcode.self_improve.approval_retention_plan import (
    InvalidRetentionPlan, RetentionLimits, prepare_retention_plan, replay_retention_plan,
)


@pytest.fixture
def limits():
    return RetentionLimits(max_source_values=50_000, max_source_bytes=2_000_000,
                           max_active_values=10_000, max_active_bytes=500_000,
                           max_archive_values=30, max_archive_bytes=500_000,
                           max_manifest_bytes=2_000_000, max_depth=64)


def source():
    return {"pending": {"status": "pending", "payload": {"x": [1]}},
            "authority": {"status": "approved", "decided_by": "human"},
            "old-a": {"status": "rejected", "payload": {"x": [2, 3]}},
            "old-b": {"status": "rejected", "payload": {"x": [4, 5]}}}


def roles():
    return {"pending": "pending", "authority": "authority",
            "old-a": "cold_history", "old-b": "cold_history"}


def plan(limits):
    return prepare_retention_plan(source(), roles=roles(), archive_ids=("old-a", "old-b"), limits=limits)


def replay(proposal, limits, retrieved=None):
    return replay_retention_plan(manifest_json=proposal.manifest_json,
                                active_json=proposal.active_json,
                                retrieved=({a.sha256: a.content for a in proposal.archives}
                                           if retrieved is None else retrieved), limits=limits)


def test_complete_valid_history_replay_detaches_caller_data(limits):
    original = source()
    proposal = prepare_retention_plan(original, roles=roles(), archive_ids=("old-a", "old-b"), limits=limits)
    original["old-a"]["payload"]["x"].append(99)
    assert replay(proposal, limits) == source()
    assert set(json.loads(proposal.active_json)) == {"pending", "authority"}


@pytest.mark.parametrize("key", ["pending", "authority"])
def test_protected_requests_and_authority_records_cannot_archive(limits, key):
    with pytest.raises(InvalidRetentionPlan):
        prepare_retention_plan(source(), roles=roles(), archive_ids=(key,), limits=limits)


def test_pending_status_vetoes_incorrect_history_classification(limits):
    assigned = roles(); assigned["pending"] = "cold_history"
    with pytest.raises(InvalidRetentionPlan):
        prepare_retention_plan(source(), roles=assigned, archive_ids=("pending",), limits=limits)


def test_unknown_role_retained_and_never_silently_selected(limits):
    assigned = roles(); assigned["old-a"] = "unknown"
    proposal = prepare_retention_plan(source(), roles=assigned, archive_ids=("old-b",), limits=limits)
    assert "old-a" in json.loads(proposal.active_json)
    assert replay(proposal, limits) == source()
    with pytest.raises(InvalidRetentionPlan):
        prepare_retention_plan(source(), roles=assigned, archive_ids=("old-a",), limits=limits)


@pytest.mark.parametrize("selected", [("old-a", "old-a"), ("absent",)])
def test_duplicate_or_missing_id_fails_without_mutation(limits, selected):
    original = source(); before = json.dumps(original)
    with pytest.raises(InvalidRetentionPlan):
        prepare_retention_plan(original, roles=roles(), archive_ids=selected, limits=limits)
    assert json.dumps(original) == before


def test_complete_role_coverage_required(limits):
    assigned = roles(); del assigned["old-a"]
    with pytest.raises(InvalidRetentionPlan):
        prepare_retention_plan(source(), roles=assigned, archive_ids=(), limits=limits)


def test_whole_history_over_sc_j04_ceiling_has_bounded_plan(limits):
    state = {f"old-{i:05}": {"status": "rejected", "payload": [0] * 15}
             for i in range(600)}
    assigned = {key: "cold_history" for key in state}
    proposal = prepare_retention_plan(state, roles=assigned, archive_ids=tuple(state), limits=limits)
    assert proposal.active_json == b"{}"
    assert len(proposal.archives) == 600
    assert replay(proposal, limits) == state


def test_deterministic_bounded_shards_and_selection_order(limits):
    tight = replace(limits, max_archive_values=9)
    left = plan(tight)
    right = prepare_retention_plan(dict(reversed(list(source().items()))), roles=roles(),
                                   archive_ids=("old-b", "old-a"), limits=tight)
    assert left == right
    assert len(left.archives) == 2
    assert replay(left, tight) == source()


@pytest.mark.parametrize("field,value", [("max_active_values", 2), ("max_active_bytes", 2),
                                         ("max_archive_values", 2), ("max_archive_bytes", 2),
                                         ("max_source_values", 2), ("max_source_bytes", 2),
                                         ("max_manifest_bytes", 2)])
def test_capacity_failure_never_mutates_source(limits, field, value):
    original = source(); before = json.dumps(original)
    with pytest.raises(InvalidRetentionPlan):
        prepare_retention_plan(original, roles=roles(), archive_ids=("old-a",),
                               limits=replace(limits, **{field: value}))
    assert json.dumps(original) == before


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), (1, 2), object()])
def test_unsupported_values_fail_without_partial_plan(limits, bad):
    state = source(); state["old-a"]["payload"] = bad
    with pytest.raises(InvalidRetentionPlan):
        prepare_retention_plan(state, roles=roles(), archive_ids=("old-a",), limits=limits)


def test_cycles_and_shared_expansion_are_bounded(limits):
    state = source(); cycle = []; cycle.append(cycle)
    state["old-a"]["payload"] = cycle
    with pytest.raises(InvalidRetentionPlan):
        prepare_retention_plan(state, roles=roles(), archive_ids=("old-a",), limits=limits)
    shared = [1] * 20
    state["old-a"]["payload"] = [shared, shared]
    with pytest.raises(InvalidRetentionPlan):
        prepare_retention_plan(state, roles=roles(), archive_ids=("old-a",),
                               limits=replace(limits, max_source_values=30))


@pytest.mark.parametrize("fault", ["missing", "extra", "truncated", "wrong_bytes"])
def test_archive_retrieval_failure_never_returns_partial_history(limits, fault):
    proposal = plan(limits); retrieved = {a.sha256: a.content for a in proposal.archives}
    key = proposal.archives[0].sha256
    if fault == "missing":
        del retrieved[key]
    elif fault == "extra":
        retrieved["unexpected"] = b"{}"
    elif fault == "truncated":
        retrieved[key] = retrieved[key][:-1]
    else:
        retrieved[key] = b"{}"
    with pytest.raises(InvalidRetentionPlan):
        replay(proposal, limits, retrieved)


@pytest.mark.parametrize("field", ["source_sha256", "source_values", "source_ids", "roles", "active", "archives"])
def test_manifest_tampering_fails_closed(limits, field):
    proposal = plan(limits)
    manifest = json.loads(proposal.manifest_json); manifest[field] = None
    corrupt = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    with pytest.raises(InvalidRetentionPlan):
        replay(replace(proposal, manifest_json=corrupt), limits)


def test_active_retrieval_and_duplicate_keys_rejected(limits):
    proposal = plan(limits)
    for content in (b"{}", b'{"a":1,"a":2}', b'{"x":NaN}', b'[]'):
        with pytest.raises(InvalidRetentionPlan):
            replay(replace(proposal, active_json=content), limits)


@pytest.mark.parametrize("cut", ["prepared", "archive_uploaded", "manifest_uploaded", "retrieval_verified"])
def test_precommit_crash_protocol_model_retains_original_authoritative_state(limits, cut):
    # MODEL ONLY: no production committer exists in this unit. Actual fsync,
    # process crashes and rename ordering require peer-owned execution canaries.
    authoritative = json.dumps(source()).encode(); before = authoritative
    proposal = plan(limits)
    artifacts = {}
    if cut != "prepared":
        artifacts = {a.sha256: a.content for a in proposal.archives}
    if cut == "retrieval_verified":
        assert replay(proposal, limits, artifacts) == source()
    assert authoritative == before


def test_headroom_is_explicit_and_not_inferred(limits):
    with pytest.raises(InvalidRetentionPlan):
        plan(replace(limits, max_active_values=1))
    assert plan(limits).active_json


@pytest.mark.parametrize("change", [{"max_active_values": 10001}, {"max_depth": 65},
                                     {"max_source_values": True}, {"max_archive_bytes": 0}])
def test_invalid_policy_limits_rejected(limits, change):
    with pytest.raises(InvalidRetentionPlan):
        replace(limits, **change)


def test_encoder_failure_preserves_caller_source(limits, monkeypatch):
    import sugarcode.self_improve.approval_retention_plan as helper
    original = source(); before = repr(original)
    def failure(*args, **kwargs):
        raise ValueError("simulated encoding failure")
    monkeypatch.setattr(helper.json, "dumps", failure)
    with pytest.raises(InvalidRetentionPlan):
        prepare_retention_plan(original, roles=roles(), archive_ids=("old-a",), limits=limits)
    assert repr(original) == before


def test_aggregate_replay_budget_cannot_be_bypassed_by_small_shards(limits):
    proposal = plan(limits)
    with pytest.raises(InvalidRetentionPlan):
        replay(proposal, replace(limits, max_source_values=10))


def test_depth_and_hostile_subclass_are_not_converted(limits):
    class Hostile(dict):
        def items(self):
            pytest.fail("subclass conversion invoked")
    state = source(); state["old-a"]["payload"] = Hostile()
    with pytest.raises(InvalidRetentionPlan):
        prepare_retention_plan(state, roles=roles(), archive_ids=("old-a",), limits=limits)
    nested = []
    for _ in range(65):
        nested = [nested]
    state["old-a"]["payload"] = nested
    with pytest.raises(InvalidRetentionPlan):
        prepare_retention_plan(state, roles=roles(), archive_ids=("old-a",), limits=limits)


def test_empty_and_no_selection_replay_are_lossless(limits):
    empty = prepare_retention_plan({}, roles={}, archive_ids=(), limits=limits)
    assert not empty.archives
    assert replay(empty, limits) == {}
    original = source()
    keep = prepare_retention_plan(original, roles=roles(), archive_ids=(), limits=limits)
    assert replay(keep, limits) == original


def test_repeated_descriptor_is_rejected(limits):
    proposal = plan(limits); manifest = json.loads(proposal.manifest_json)
    manifest["archives"].append(manifest["archives"][0])
    corrupt = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    with pytest.raises(InvalidRetentionPlan):
        replay(replace(proposal, manifest_json=corrupt), limits)
