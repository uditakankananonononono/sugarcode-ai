import pytest
from sugarcode.modules.microbiome_rx import *
def community(): return {"Faecalibacterium":.1,"Bacteroides":.2,"Escherichia":.1,"Lactobacillus":.15,"Akkermansia":.1,"Bifidobacterium":.2}
def test_real_coupled_ode_and_diet_response():
 a=simulate_metabolic_community(community(),days=2,diet={"fiber":.2}); b=simulate_metabolic_community(community(),days=2,diet={"fiber":2}); assert a["solver"]["success"] and a["final_metabolites"]!=b["final_metabolites"]
def test_antibiotic_changes_species():
 a=simulate_metabolic_community(community(),days=2); b=simulate_metabolic_community(community(),days=2,antibiotic_effects={"Escherichia":.8}); assert b["final_relative"]["Escherichia"]<a["final_relative"]["Escherichia"]
def test_real_intervention_optimizer():
 r=optimize_intervention(community(),{"butyrate":.1},days=2); assert r["evaluations"]>10 and 0<=r["diet"]["fiber"]<=3
def test_exactly_fifty_case_derived_diagnostics():
 r=analyze_microbiome(community(),{"butyrate":.1},days=2); assert len(r["diagnostics"])==50 and len(set(r["diagnostics"]))==50
 assert {"optimization_objective","optimized_fiber","optimized_sugar","optimization_evaluations"} <= set(r["diagnostics"])
def test_actionable_and_honest():
 r=analyze_microbiome(community(),{"acetate":.2},days=1); assert r["diagnostic_count"]==50 and len(r["lab_plan"])==4 and "no clinical response claim" in r["optimization"]["simulation"]["model_status"]
def test_legacy_api_remains(): assert simulate_community(community(),days=1)["trajectory"] and design_intervention(current_profile=community())["recommended"]
def test_validation_errors():
 with pytest.raises(ValueError,match="unknown species"): validate_community({"bad":1},{"fiber":1})
 with pytest.raises(ValueError,match="antibiotic"): simulate_metabolic_community(community(),antibiotic_effects={"bad":.5})
