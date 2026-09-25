"""Module 119 robotic_flow: calibration truthfulness, lineage soundness, scheduler contracts."""
import pytest
from sugarcode.modules.robotic_flow import (pipette_plan, schedule_run, sample_lineage,
                                            reagent_status, LIQUID_CLASSES)


def test_unknown_liquid_rejected_not_miscalibrated():
    with pytest.raises(KeyError):
        pipette_plan([{"source": "A1", "dest": "B1", "volume_ul": 10, "liquid": "mercury"}])
    # water identity: 10 ul at 200 ul/s = .05s aspirate; estimate 2*.05+3 = 3.1 s
    s = pipette_plan([{"source": "A1", "dest": "B1", "volume_ul": 10}])["steps"][0]
    assert s["aspirate_speed_ul_s"] == 200 and s["estimated_s"] == 3.1


def test_lineage_traceability_is_sound():
    assert not sample_lineage([], [{"op": "mix", "inputs": ["ghost"], "output": "b"}])["traceable"]
    r = sample_lineage(["a"], [{"op": "mix", "inputs": ["a"], "output": "b"}])
    assert r["traceable"] and r["unknown_parents"] == []


def test_scheduler_input_contracts():
    with pytest.raises(ValueError, match="unknown dependencies"):
        schedule_run([{"id": "a", "instrument": "i", "duration_min": 1, "after": ["missing"]}])
    with pytest.raises(ValueError, match="duplicate"):
        schedule_run([{"id": "a", "instrument": "i", "duration_min": 1},
                      {"id": "a", "instrument": "i", "duration_min": 2}])
    # real cycle still detected
    with pytest.raises(ValueError, match="cycle"):
        schedule_run([{"id": "a", "instrument": "i", "duration_min": 1, "after": ["b"]},
                      {"id": "b", "instrument": "i", "duration_min": 1, "after": ["a"]}])


def test_scheduler_respects_instrument_sharing_and_deps():
    r = schedule_run([{"id": "a", "instrument": "pip", "duration_min": 5},
                      {"id": "b", "instrument": "pip", "duration_min": 5},
                      {"id": "c", "instrument": "read", "duration_min": 10, "after": ["a"]}])
    tl = {x["id"]: x for x in r["timeline"]}
    assert tl["b"]["start_min"] >= tl["a"]["end_min"]  # shared instrument serialized
    assert tl["c"]["start_min"] >= tl["a"]["end_min"]  # dependency honored
    assert r["makespan_min"] == 15.0
    assert r["instrument_utilization"]["pip"] == pytest.approx(10 / 15, abs=1e-3)  # busy/makespan


def test_reagent_decay_identity():
    assert reagent_status(5, 5)["activity_fraction"] == pytest.approx(0.5)
    assert not reagent_status(20, 5)["usable"]
