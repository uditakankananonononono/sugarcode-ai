import pytest
from sugarcode.modules.phage_tx import *
def test_real_stiff_coevolution_solver_tracks_resistance():
 r=simulate_coevolution({"hours":12,"bacteria":1e6,"phage":1e7,"mutation_rate":1e-5}); assert r["solver"]["success"] and len(r["trajectory"])>20 and r["final_resistant_fraction"]>=0
def test_exact_cocktail_optimizer_and_receptor_coverage():
 r=optimize_cocktail("Escherichia_coli",{"T4":.9,"T7":.8,"lambda_vir":.7},max_phages=3)
 assert r["solver"]=="exact_subset_enumeration" and r["evaluated_cocktails"]==7
 assert any(x["phage_count"]>1 for x in r["ranking"]) and r["ranking"][0]["score"]!=r["ranking"][1]["score"]
 assert r["selected"]["receptor_count"]>=2
def test_susceptibility_changes_optimized_score():
 a=optimize_cocktail("Escherichia_coli",{"T4":.9,"T7":.7,"lambda_vir":.6}); b=optimize_cocktail("Escherichia_coli",{"T4":.3,"T7":.2,"lambda_vir":.1}); assert a["selected"]["score"]>b["selected"]["score"]
def test_exactly_fifty_one_case_derived_diagnostics():
 r=design_phage_therapy("Escherichia_coli",{"T4":.9,"T7":.8,"lambda_vir":.7},{"hours":12}); assert len(r["diagnostics"])==51 and len(set(r["diagnostics"]))==51
def test_end_to_end_has_modifications_monitoring_and_honest_status():
 r=design_phage_therapy("Escherichia_coli",{"T4":.8,"T7":.7,"lambda_vir":.6},{"hours":6}); assert r["diagnostic_count"]==51 and r["modification_suggestions"] and len(r["monitoring_plan"])==4 and "no therapeutic efficacy claim" in r["simulation"]["model_status"]
def test_legacy_apis_remain_available(): assert match_phages("Escherichia_coli")["best"] and evolve_cocktail("Escherichia_coli",rounds=2)["evolution_history"]
def test_validation_errors_are_informative():
 with pytest.raises(ValueError,match="mutation_rate"): validate_phage_parameters({"mutation_rate":2})
 with pytest.raises(ValueError,match="susceptibility"): optimize_cocktail("Escherichia_coli",{"T4":2})
 with pytest.raises(ValueError,match="unavailable"): optimize_cocktail("Escherichia_coli",{"phiKZ":.5})
