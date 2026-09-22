import pytest
from sugarcode.modules.virtual_cell import *

def test_fba_conserves_mass_and_predicts_growth():
 m=demo_model(); r=fba(m); assert r["status"]=="optimal" and r["objective"]>0 and all(abs(x)<1e-5 for x in m.S@list(r["fluxes"].values()))

def test_environmental_changes_alter_growth_phenotype():
 r=environment_response(demo_model(),{"rich":{},"starved":{"GLC_UP":(0,0)}}); assert r["conditions"]["rich"]["growth"]>0 and r["conditions"]["starved"]["growth"]==0 and r["conditions"]["starved"]["phenotype"]=="no growth"

def test_grn_is_deterministic_and_couples_to_flux_bounds():
 g=regulatory_state(["sensor","resp"],[("sensor","sensor",1),("sensor","resp",1)],{"sensor":1}); assert g["steady_state"]=={"sensor":1,"resp":1} and g["converged"]
 on=couple_grn_metabolism(demo_model(),["sensor","resp"],[("sensor","sensor",1),("sensor","resp",1)],{"RESP":"resp"},{"sensor":1}); off=couple_grn_metabolism(demo_model(),["sensor","resp"],[],{"RESP":"resp"}); assert on["predicted_growth"]>off["predicted_growth"] and off["disabled_reactions"]==["RESP"]

def test_perturbation_screen_ranks_growth_impacts():
 r=perturbation_screen(demo_model()); assert len(r["perturbations"])==6 and r["perturbations"][0]["growth_ratio"]<=r["perturbations"][-1]["growth_ratio"] and "GLC_UP" in r["essential_reactions"]

def test_end_to_end_report_exposes_system_wide_predictions_and_limits():
 r=virtual_cell_report(); assert r["baseline"]["objective"]>0 and r["growth"]["trajectory"] and r["regulatory_metabolic_coupling"]["predicted_growth"]>0 and len(r["environment"]["conditions"])==2 and len(r["limitations"])==2

def test_legacy_apis_remain_available():
 m=demo_model(); assert fba(m)["status"]=="optimal" and gene_knockout(m,"RESP")["knocked_out"]=="RESP" and simulate_growth(m,hours=.5)["final_biomass"]>0

def test_validation_errors_are_informative():
 with pytest.raises(ValueError,match="genes"): regulatory_state([],[])
 with pytest.raises(ValueError,match="unknown genes"): regulatory_state(["a"],[("b","a",1)])
 with pytest.raises(ValueError,match="unknown reaction"): couple_grn_metabolism(demo_model(),["a"],[],{"fake":"a"})
 with pytest.raises(ValueError,match="unknown reactions"): perturbation_screen(demo_model(),["fake"])
