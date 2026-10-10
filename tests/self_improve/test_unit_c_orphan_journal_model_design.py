"""DESIGN-ONLY synthetic consistency tests, authored NOT RUN.

No product imports, recovery implementation, deletion/adoption, or filesystem IO.
Assertions inspect proposed expectations, not actual crash durability behavior.
"""
import pytest

# cut, JSON, destination, temp, consumption (engine-coordinated path only)
CUTS = (
    ("temp_fsynced", "R0", "absent", "complete", "C0"),
    ("name_published", "R0", "complete", "complete", "C0"),
    ("published_dir_fsynced", "R0", "complete", "complete", "C0"),
    ("temp_removed_fsynced", "R0", "complete", "absent", "C0"),
    ("before_registry_commit", "R0", "complete", "absent", "C0"),
    ("registry_committed", "R1", "complete", "absent", "C1"),
)


@pytest.mark.parametrize("cut,registry,dest,temp,consumption", CUTS)
def test_design_six_cut_state_consistency(cut, registry, dest, temp, consumption):
    assert (registry == "R1") == (consumption == "C1")
    if registry == "R1":
        assert dest == "complete" and temp == "absent"
    if cut == "temp_fsynced":
        assert dest == "absent"
    assert cut in {row[0] for row in CUTS}


def test_design_postreplace_failure_is_not_unused():
    observed = {"registry": "R1", "consumption": "C1", "destination": "complete",
                "registry_committed_checkpoint": False, "durability": "unknown"}
    assert observed["consumption"] == "C1"
    assert not observed["registry_committed_checkpoint"]
    assert observed["durability"] != "proven"


@pytest.mark.parametrize("registry,expected", [("R0", "orphan_hold"),
                                              ("R1", "committed_observation"),
                                              ("invalid", "hold")])
def test_design_exception_none_needs_authoritative_inspection(registry, expected):
    observation = {"error_flag": None, "registry": registry, "decision": expected,
                   "automatic_retry": False}
    assert observation["error_flag"] is None
    assert not observation["automatic_retry"]
    assert observation["decision"] != "retry"


def test_design_final_sync_failure_without_temp_is_orphan():
    observed = {"registry": "R0", "destination": "complete", "temp": "absent",
                "consumption": "C0", "published": True}
    assert observed["published"] and observed["temp"] == "absent"
    assert observed["registry"] == "R0" and observed["consumption"] == "C0"


def test_design_eexist_blocks_same_next_version_without_overwrite():
    observed = {"registry_versions": [1, 2], "next_version": 3,
                "unreferenced_files": ["demo_v3.py"], "authorized_effect": None}
    assert len(observed["registry_versions"]) + 1 == observed["next_version"]
    assert "demo_v3.py" in observed["unreferenced_files"]
    assert observed["authorized_effect"] is None


def test_design_inactive_version_remains_referenced():
    versions = [{"version": 1, "file": "v1.py"}, {"version": 2, "file": "v2.py"}]
    active = 1
    referenced = {row["file"] for row in versions}
    assert active != 2 and "v2.py" in referenced
    assert referenced == {"v1.py", "v2.py"}


@pytest.mark.parametrize("mismatch", ["generation", "registry_digest", "source_digest",
                                      "gate_identity", "approval_binding", "reference_set"])
def test_design_stale_or_malicious_observation_holds(mismatch):
    report = {"mismatch": mismatch, "authority": "unverified", "decision": "HOLD"}
    assert report["decision"] == "HOLD" and report["authority"] != "verified"


@pytest.mark.parametrize("journal,registry", [("INTENT", "R1"), ("COMMITTED", "R0"),
                                              ("partial", "R0"), ("missing", "R1")])
def test_design_journal_never_overrules_registry_readback(journal, registry):
    report = {"journal": journal, "registry": registry,
              "inspection_required": True, "automatic_delete": False}
    assert report["inspection_required"] and not report["automatic_delete"]


def test_design_direct_registry_bypass_does_not_invent_consumption():
    observed = {"registry": "R1", "engine_gate_identity": None, "consumption": "C0"}
    assert observed["engine_gate_identity"] is None and observed["consumption"] == "C0"


def test_design_rollback_preserves_versions_and_used_approval():
    old = {"versions": (1, 2), "active": 2, "used": ("activate-a",)}
    proposed = {"versions": (1, 2), "active": 1, "used": ("activate-a", "rollback-b")}
    assert proposed["versions"] == old["versions"]
    assert set(old["used"]) <= set(proposed["used"])


def test_design_no_implicit_removal_authority():
    decision = {"classification": "unreferenced", "journal": "COMMITTED",
                "owner_removal_approval": None, "permitted_removal": False}
    assert decision["owner_removal_approval"] is None
    assert not decision["permitted_removal"]
