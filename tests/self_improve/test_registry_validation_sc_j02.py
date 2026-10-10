"""Peer J02 authored cases now locally run; production wiring assessed separately."""
import json
from copy import deepcopy

import pytest

from sugarcode.self_improve.registry import FeatureRegistry
from sugarcode.self_improve.registry_validation import (
    RegistryValidationError, decode_registry_json, validate_registry_state,
)
from sc_j02_fixtures import EMPTY, legacy_states


def active_state():
    return legacy_states()[2]


def test_valid_legacy_fixture_replay_preserves_all_fields():
    for state in legacy_states():
        snapshot = deepcopy(state)
        assert validate_registry_state(state, expected_module="m1") is state
        assert state == snapshot
        assert decode_registry_json(json.dumps(state).encode(), expected_module="m1") == state


@pytest.mark.parametrize("raw", [
    '{"module":"m1","module":"m2","features":{},"proposals":{}}',
    '{"module":"m1","features":{},"proposals":{},"x":{"a":1,"a":2}}',
    '{"module":"m1","features":{},"proposals":{},"x":[{"a":1,"a":2}]}',
    '{"module":"m1","features":{},"proposals":{},"x":NaN}',
    '{"module":"m1","features":{},"proposals":{},"x":[Infinity]}',
    '{"module":"m1","features":{},"proposals":{},"x":-Infinity}',
    '{"module":"m1","features":{},"proposals":{},"x":1e9999}',
    '{"module":"m1","features":{},"proposals":{},"x":-1e9999}',
    'null', '[]', '1', 'true', '"state"', '{}', '{',
    '{"module":"m1","features":{},"proposals":{}} trailing',
    b'\xff', b'\xff\xfe{\x00}\x00', b'\xef\xbb\xbf{}',
])
def test_ambiguous_nonfinite_nonobject_or_malformed_json_refused(raw):
    with pytest.raises(RegistryValidationError):
        decode_registry_json(raw, expected_module="m1")


@pytest.mark.parametrize("active", [True, False, 0, -1, 2, 1.0, "1", [], {}])
def test_invalid_active_version_reference_refused(active):
    state = active_state()
    state["features"]["demo"]["active_version"] = active
    with pytest.raises(RegistryValidationError):
        validate_registry_state(state, expected_module="m1")


@pytest.mark.parametrize("numbers", [[2], [1, 1], [1, 3], [2, 1], [True], [1.0], ["1"]])
def test_duplicate_reordered_gapped_or_mistyped_versions_refused(numbers):
    state = active_state()
    original = state["features"]["demo"]["versions"][0]
    state["features"]["demo"]["versions"] = [dict(original, version=n) for n in numbers]
    with pytest.raises(RegistryValidationError):
        validate_registry_state(state, expected_module="m1")


@pytest.mark.parametrize("field,bad", [
    ("file", None), ("sha256", "a" * 63), ("sha256", "A" * 64),
    ("kind", []), ("gap_signature", None), ("approval_id", None),
    ("approval_id", ""), ("activated_at", True), ("activated_at", -1),
    ("dispatch_count", True), ("dispatch_count", -1), ("dispatch_count", 1.0),
    ("last_dispatched_at", None), ("rolled_back_at", 2), ("rollback_approval_id", "a2"),
])
def test_invalid_version_fields_refused(field, bad):
    state = active_state()
    state["features"]["demo"]["versions"][0][field] = bad
    with pytest.raises(RegistryValidationError):
        validate_registry_state(state, expected_module="m1")


@pytest.mark.parametrize("field,bad", [
    ("name", "../other"), ("kind", ""), ("gap_signature", []),
    ("code_sha256", "bad"), ("test_sha256", False), ("code_file", ""),
    ("test_file", 3), ("approval_id", {}), ("status", "approved"),
    ("status", []), ("created_at", True), ("created_at", -1),
])
def test_invalid_proposal_fields_refused(field, bad):
    state = active_state()
    state["proposals"]["k1"][field] = bad
    with pytest.raises(RegistryValidationError):
        validate_registry_state(state, expected_module="m1")


@pytest.mark.parametrize("section", ["features", "proposals"])
@pytest.mark.parametrize("bad", [None, [], "state", 1])
def test_registry_collection_shape_refused(section, bad):
    state = deepcopy(EMPTY)
    state[section] = bad
    with pytest.raises(RegistryValidationError):
        validate_registry_state(state, expected_module="m1")


@pytest.mark.parametrize("target", ["root", "feature", "version", "proposal"])
def test_every_required_field_is_required(target):
    base = active_state()
    def get(state):
        return {"root": state, "feature": state["features"]["demo"],
                "version": state["features"]["demo"]["versions"][0],
                "proposal": state["proposals"]["k1"]}[target]
    for field in get(base):
        if field == "dispatch_count":
            continue
        state = deepcopy(base)
        del get(state)[field]
        with pytest.raises(RegistryValidationError):
            validate_registry_state(state, expected_module="m1")


def test_wrong_module_and_unsafe_ids_refused():
    with pytest.raises(RegistryValidationError):
        validate_registry_state(deepcopy(EMPTY), expected_module="m2")
    for section in ("features", "proposals"):
        for bad in ("", "../demo", "demo/name", "demo\\name", "demo.txt", "__"):
            state = active_state()
            old = "demo" if section == "features" else "k1"
            state[section][bad] = state[section].pop(old)
            with pytest.raises(RegistryValidationError):
                validate_registry_state(state, expected_module="m1")


def test_unknown_finite_json_fields_preserved_and_legacy_count_optional():
    state = active_state()
    state["metadata"] = {"nested": [True, None, 1.25]}
    del state["features"]["demo"]["versions"][0]["dispatch_count"]
    assert validate_registry_state(state, expected_module="m1") is state


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), object(), (1, 2)])
def test_invalid_unknown_extension_values_refused(bad):
    state = deepcopy(EMPTY)
    state["metadata"] = {"nested": [bad]}
    with pytest.raises(RegistryValidationError):
        validate_registry_state(state, expected_module="m1")


def test_custom_container_or_value_hooks_never_called():
    class Hostile(dict):
        def items(self):
            raise AssertionError("custom items hook executed")
    class HostileNumber(int):
        def __lt__(self, other):
            raise AssertionError("custom comparison executed")
    for value in (Hostile(EMPTY), dict(EMPTY, extra=Hostile()), dict(EMPTY, extra=HostileNumber(1))):
        with pytest.raises(RegistryValidationError):
            validate_registry_state(value, expected_module="m1")


def test_cycles_refused_shared_acyclic_values_allowed():
    state = deepcopy(EMPTY)
    state["cycle"] = state
    with pytest.raises(RegistryValidationError):
        validate_registry_state(state, expected_module="m1")
    state = deepcopy(EMPTY)
    shared = {"finite": [1, 2]}
    state.update(first=shared, second=shared)
    assert validate_registry_state(state, expected_module="m1") is state


def test_invalid_read_bytes_are_unchanged(tmp_path):
    path = tmp_path / "registry.json"
    raw = b'{"module":"m1","features":{},"proposals":{},"x":NaN}'
    path.write_bytes(raw)
    with pytest.raises(RegistryValidationError):
        decode_registry_json(path.read_bytes(), expected_module="m1")
    assert path.read_bytes() == raw


def test_original_decoder_accepts_duplicate_and_nonfinite_canaries():
    raw = '{"module":"m1","features":{},"proposals":{},"x":1,"x":NaN}'
    original = json.loads(raw)
    assert "x" in original
    with pytest.raises(RegistryValidationError):
        decode_registry_json(raw, expected_module="m1")


def test_actual_legacy_registry_lifecycle_replay(tmp_path):
    # Reads actual writer output but does not wire the validator into production.
    registry = FeatureRegistry("m1", tmp_path)
    def check():
        return decode_registry_json(registry._path.read_bytes(), expected_module="m1")
    check()
    for key, code in [("k1", 'def run(items, params=None):\n    return {"items": items}\n'),
                      ("k2", 'def run(items, params=None):\n    return {"count": len(items)}\n')]:
        registry.save_proposal(key, name="demo", kind="keyword_filter", code=code,
                               test_code="", gap_signature="sig")
        check()
        registry.set_proposal_approval(key, "a" + key)
        check()
        registry.activate(key, approval_id="a" + key)
        check()
        registry.dispatch("demo", ["x"])
        check()
    registry.rollback("demo", approval_id="rollback1")
    assert check()["features"]["demo"]["active_version"] == 1
    registry.rollback("demo", approval_id="rollback2")
    assert check()["features"]["demo"]["active_version"] is None


@pytest.mark.parametrize("target,bad", [
    ("feature", None), ("feature", []), ("versions", {}), ("versions", None),
    ("version", None), ("version", []), ("proposal", None), ("proposal", []),
])
def test_nested_registry_shape_refused(target, bad):
    state = active_state()
    if target == "feature":
        state["features"]["demo"] = bad
    elif target == "versions":
        state["features"]["demo"]["versions"] = bad
    elif target == "version":
        state["features"]["demo"]["versions"][0] = bad
    else:
        state["proposals"]["k1"] = bad
    with pytest.raises(RegistryValidationError):
        validate_registry_state(state, expected_module="m1")


def test_empty_history_cannot_have_active_version():
    state = deepcopy(EMPTY)
    state["features"]["demo"] = {"versions": [], "active_version": None}
    validate_registry_state(state, expected_module="m1")
    state["features"]["demo"]["active_version"] = 1
    with pytest.raises(RegistryValidationError):
        validate_registry_state(state, expected_module="m1")


def test_failed_state_validation_does_not_mutate_input():
    state = active_state()
    state["features"]["demo"]["active_version"] = 999
    snapshot = deepcopy(state)
    with pytest.raises(RegistryValidationError):
        validate_registry_state(state, expected_module="m1")
    assert state == snapshot


def test_rollback_then_reactivation_history_valid():
    state = legacy_states()[-1]
    old = state["features"]["demo"]["versions"][0]
    new = dict(old, version=2, approval_id="a3")
    del new["rolled_back_at"]
    del new["rollback_approval_id"]
    state["features"]["demo"]["versions"].append(new)
    state["features"]["demo"]["active_version"] = 2
    validate_registry_state(state, expected_module="m1")
    state["features"]["demo"]["active_version"] = 1
    validate_registry_state(state, expected_module="m1")
