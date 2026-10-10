"""Deterministic legacy-shaped registry fixtures; no runtime effects."""
from copy import deepcopy

EMPTY = {"module": "m1", "features": {}, "proposals": {}}
PROPOSAL = {
    "name": "demo", "kind": "keyword_filter", "gap_signature": "sig",
    "code_sha256": "a" * 64, "test_sha256": "b" * 64,
    "code_file": "/state/modules/m1/candidates/k1.py",
    "test_file": "/state/modules/m1/candidates/k1.test.py",
    "approval_id": None, "status": "proposed", "created_at": 1720000000.0,
}
VERSION = {
    "version": 1, "file": "/state/modules/m1/extensions/demo_v1.py",
    "sha256": "a" * 64, "kind": "keyword_filter", "gap_signature": "sig",
    "approval_id": "a1", "activated_at": 1720000001.0, "dispatch_count": 0,
}


def legacy_states():
    empty = deepcopy(EMPTY)
    proposed = deepcopy(EMPTY)
    proposed["proposals"]["k1"] = deepcopy(PROPOSAL)
    active = deepcopy(proposed)
    active["proposals"]["k1"]["status"] = "activated"
    active["features"]["demo"] = {"versions": [deepcopy(VERSION)], "active_version": 1}
    dispatched = deepcopy(active)
    dispatched["features"]["demo"]["versions"][0].update(
        dispatch_count=1, last_dispatched_at=1720000002.0)
    rollback = deepcopy(dispatched)
    rollback["features"]["demo"]["active_version"] = None
    rollback["features"]["demo"]["versions"][0].update(
        rolled_back_at=1720000003.0, rollback_approval_id="a2")
    return [empty, proposed, active, dispatched, rollback]
