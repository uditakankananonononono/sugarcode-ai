"""Invariant tests: region/conservation key consistency, determinism, lead-first ordering."""
from sugarcode.modules.vector_opt.core import CAPSID_REGIONS, CONSERVATION, engineer_capsid


def test_region_and_conservation_keys_match():
    assert set(CAPSID_REGIONS) == set(CONSERVATION)


def test_engineer_capsid_deterministic_and_lead_first():
    a = engineer_capsid(capsid="AAV9", seed=5)
    b = engineer_capsid(capsid="AAV9", seed=5)
    assert a["variants"] == b["variants"]
    assert a["lead"] == a["variants"][0]
    assert a["docking_summary"]["lead_receptor_gain"] == a["lead"]["receptor_affinity_gain"]
