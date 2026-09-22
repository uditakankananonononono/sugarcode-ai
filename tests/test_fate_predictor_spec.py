import pytest
from sugarcode.modules.fate_predictor import *
def test_exact_tf_subset_solver_has_live_alternatives():
 r=optimize_tf_set("fibroblast","neuron"); assert r["solver"]=="exact_subset_enumeration" and r["evaluated_subsets"]>3 and r["ranking"][0]["score"]>r["ranking"][1]["score"]
def test_conversion_changes_selected_factors():
 a=optimize_tf_set("fibroblast","neuron"); b=optimize_tf_set("fibroblast","cardiomyocyte"); assert a["selected"]["factors"]!=b["selected"]["factors"]
def test_real_ode_is_delivery_sensitive():
 f=optimize_tf_set("fibroblast","neuron")["selected"]["factors"]; a=simulate_trajectory("fibroblast","neuron",f,days=7,delivery="lentivirus"); b=simulate_trajectory("fibroblast","neuron",f,days=7,delivery="episomal"); assert a["solver"]["success"] and a["terminal_target_fraction"]>b["terminal_target_fraction"]
def test_exactly_fifty_case_derived_diagnostics():
 r=design_reprogramming("fibroblast","neuron",days=7); assert len(r["diagnostics"])==50 and len(set(r["diagnostics"]))==50
def test_single_candidate_curated_conversion_is_supported():
 r=design_reprogramming("b_cell","macrophage",days=3)
 assert r["optimization"]["evaluated_subsets"]==1 and r["optimization"]["selected"]["factors"]==["CEBPA"]
 assert r["diagnostics"]["score_margin"]==0.0 and r["diagnostic_count"]==50

def test_actionable_protocol_and_honest_status():
 r=design_reprogramming("fibroblast","cardiomyocyte",days=7); assert r["diagnostic_count"]==50 and r["protocol"] and len(r["validation"])==4 and "no regenerative" in r["simulation"]["model_status"]
def test_legacy_predictor_remains_available(): assert predict_reprogramming("fibroblast","neuron")["transcription_factors"]
def test_validation_errors_are_informative():
 with pytest.raises(ValueError,match="unsupported source"): validate_conversion("x","neuron","mRNA")
 with pytest.raises(ValueError,match="must differ"): validate_conversion("neuron","neuron","mRNA")
 with pytest.raises(ValueError,match="factors"): simulate_trajectory("fibroblast","neuron",[],days=2)
