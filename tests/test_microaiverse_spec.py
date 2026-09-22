import pytest
from sugarcode.modules.microaiverse import *
def target(): return {"name":"uncultured_X","uptake":{"glucose":1},"requirements":{"cobalamin":.2,"heme":.1}}
def partners(): return [{"name":"donor_A","uptake":{"glucose":.2},"secretion":{"cobalamin":.3,"heme":.2}},{"name":"competitor_B","uptake":{"glucose":.9},"secretion":{"cobalamin":.05}}]
def test_real_highs_lp_meets_medium_requirements_at_minimum_cost():
 r=optimize_medium(target(),{"cobalamin":2,"heme":3},budget=1); assert r["solver"].startswith("scipy HiGHS") and r["optimal"] and all(r["requirements_met"].values())
def test_partner_ranking_uses_crossfeeding_and_competition():
 r=rank_coculture_partners(target(),partners()); assert r["selected"]["partner"]=="donor_A" and r["ranking"][0]["net_crossfeeding_score"]>r["ranking"][1]["net_crossfeeding_score"]
def test_real_coculture_ode_grows_target():
 r=simulate_coculture(target(),partners()[0],{"cobalamin":.2,"heme":.1},hours=24); assert r["solver"]["success"] and r["target_final_biomass"]>.01
def test_exactly_fifty_case_derived_diagnostics():
 r=solve_cultivation(target(),partners(),{"cobalamin":2,"heme":3},hours=24); assert len(r["diagnostics"])==50 and len(set(r["diagnostics"]))==50
def test_end_to_end_is_actionable_and_honest():
 r=solve_cultivation(target(),partners(),{"cobalamin":2,"heme":3},hours=12); assert r["diagnostic_count"]==50 and len(r["lab_plan"])==4 and "no cultivation success claim" in r["simulation"]["model_status"]
def test_legacy_plan_remains_available(): assert cultivation_plan("microbe","auxotroph",["vitamin_B12"])["media_recipe"]["supplements"]
def test_validation_errors_are_informative():
 with pytest.raises(ValueError,match="known metabolites"): validate_flux_model({"name":"x","uptake":{"bad":1}})
 with pytest.raises(ValueError,match="missing supplement costs"): optimize_medium(target(),{"heme":1})
 with pytest.raises(ValueError,match="non-empty"): rank_coculture_partners(target(),[])
