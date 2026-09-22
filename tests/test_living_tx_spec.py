import pytest
from sugarcode.modules.living_tx import *
def test_chassis_ranking_has_live_alternatives():
 low=rank_designs("oxalate_decarboxylase",dose_cfu=1e6); high=rank_designs("GLP-1",dose_cfu=1e11)
 assert len(low["ranking"])==4 and low["selected"]["chassis"]!=high["selected"]["chassis"]
 assert [x["chassis"] for x in low["ranking"]] != [x["chassis"] for x in high["ranking"]]
def test_real_gut_community_ode_is_dose_sensitive():
 a=simulate_gut_community("Lactobacillus","IL-10",dose_cfu=1e6,days=2); b=simulate_gut_community("Lactobacillus","IL-10",dose_cfu=1e10,days=2); assert a["solver"]["success"] and b["terminal_compound"]>a["terminal_compound"]
def test_containment_risk_has_independent_components_and_controls():
 s=simulate_gut_community("E_coli_Nissle","GLP-1",days=1); r=containment_risk("E_coli_Nissle","GLP-1",s); assert 0<r["combined_risk"]<1 and len(r["required_controls"])==4
def test_exactly_fifty_case_derived_diagnostics():
 r=design_living_therapy("IL-10",days=2); assert len(r["diagnostics"])==50 and len(set(r["diagnostics"]))==50
def test_end_to_end_is_actionable_and_honest():
 r=design_living_therapy("phenylalanine_degradase",days=1); assert r["diagnostic_count"]==50 and len(r["development_plan"])==4 and "no clinical success prediction" in r["simulation"]["model_status"]
def test_legacy_design_remains_available(): assert design_living_therapeutic("IL-22")["genetic_program"]["containment"]
def test_validation_errors_are_informative():
 with pytest.raises(ValueError,match="payload"): validate_design_inputs("fake","Lactobacillus",1e9)
 with pytest.raises(ValueError,match="chassis"): validate_design_inputs("IL-10","fake",1e9)
 with pytest.raises(ValueError,match="dose_cfu"): validate_design_inputs("IL-10","Lactobacillus",1)
