import pytest
from sugarcode.modules.fate_predictor import *

def test_curated_map_matches_literature_factors():
    assert predict_reprogramming("fibroblast","neuron")["transcription_factors"]==["ASCL1","BRN2","MYT1L"]
    assert predict_reprogramming("fibroblast","ipsc")["transcription_factors"]==["OCT4","SOX2","KLF4","MYC"]
    assert predict_reprogramming("b_cell","macrophage")["transcription_factors"]==["CEBPA"]

def test_optimizer_rediscovers_published_sets():
    assert optimize_tf_set("fibroblast","neuron")["selected"]["factors"]==["ASCL1","BRN2","MYT1L"]
    assert optimize_tf_set("b_cell","macrophage")["selected"]["factors"]==["CEBPA"]
    assert set(optimize_tf_set("fibroblast","cardiomyocyte")["selected"]["factors"])>={"GATA4","MEF2C","TBX5"}

def test_delivery_scales_success():
    lenti=predict_reprogramming("fibroblast","neuron","lentivirus")["estimated_success_rate"]
    sm=predict_reprogramming("fibroblast","neuron","small_molecule")["estimated_success_rate"]
    assert lenti==0.35 and sm==pytest.approx(0.35*0.5,abs=1e-3) and lenti>sm

def test_trajectory_invariants():
    s=simulate_trajectory("fibroblast","neuron",["ASCL1","BRN2","MYT1L"])
    r=s["trajectory"]
    assert s["solver"]["success"] and r[0]["source_fraction"]==pytest.approx(1)
    assert all(0<=x["target_fraction"]<=1 for x in r)
    assert s["terminal_target_fraction"]==r[-1]["target_fraction"]

def test_diagnostics_exactly_50():
    d=design_reprogramming("fibroblast","neuron")
    assert d["diagnostic_count"]==50 and len(d["diagnostics"])==50

def test_invalid_inputs_rejected():
    with pytest.raises(ValueError): validate_conversion("fibroblast","fibroblast","mRNA")
    with pytest.raises(ValueError): simulate_trajectory("fibroblast","neuron",["NOTATF"])
