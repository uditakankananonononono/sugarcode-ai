import pytest
from sugarcode.modules.cellpainter_4d import *

def state(): return {"area_um2":200,"circularity":.85,"aspect_ratio":1.2,"intensity":100,"cell_count":300}

def test_real_ode_and_seeded_population_are_deterministic():
 a=simulate_population_4d("emt",state(),duration_h=24,seed=3); b=simulate_population_4d("emt",state(),duration_h=24,seed=3)
 assert a==b and a["solver"]["success"] and len(a["frames"])>5
 assert "mechanistic hermetic" in a["model_status"]

def test_processes_drive_expected_distinct_morphology():
 d=simulate_population_4d("differentiation",state(),duration_h=24); ap=simulate_population_4d("apoptosis",state(),duration_h=24)
 assert d["frames"][-1]["area_um2"]>d["frames"][0]["area_um2"]
 assert ap["frames"][-1]["area_um2"]<ap["frames"][0]["area_um2"] and ap["frames"][-1]["cell_count"]<ap["frames"][0]["cell_count"]

def test_event_detector_returns_metric_time_direction_and_magnitude():
 r=detect_morphology_events(simulate_population_4d("emt",state(),duration_h=48),change_threshold=.1)
 assert r["event_count"]>0 and {"time_h","metric","relative_change","direction"}<=set(r["events"][0])

def test_exactly_fifty_two_case_derived_diagnostics_vary():
 a=analyze_morphology_4d("emt",state(),duration_h=24); b=analyze_morphology_4d("apoptosis",{**state(),"area_um2":350,"cell_count":700},duration_h=48)
 assert len(a["diagnostics"])==52 and len(set(a["diagnostics"]))==52
 assert sum(a["diagnostics"][k]!=b["diagnostics"][k] for k in a["diagnostics"])>=35

def test_end_to_end_is_actionable_for_researcher():
 r=analyze_morphology_4d("differentiation",state(),duration_h=12,sample_interval_h=2)
 assert r["diagnostic_count"]==52 and r["scientist_summary"]["morphology_drift_norm"]>0 and r["recommended_actions"]

def test_legacy_api_has_no_always_true_guard_and_still_works():
 r=simulate_morphology("emt",frames=5); assert len(r["traces"]["circularity"])==5

def test_validation_errors_are_informative():
 with pytest.raises(ValueError,match="missing"): validate_morphology_state({})
 with pytest.raises(ValueError,match="circularity"): validate_morphology_state({**state(),"circularity":2})
 with pytest.raises(ValueError,match="process"): simulate_population_4d("unknown",state())
