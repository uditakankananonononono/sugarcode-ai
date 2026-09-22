import pytest
from sugarcode.modules.stability_ai import *
def construct(): return {"mode":"plasmid","burden":.5,"size_kb":6,"toxic":True,"copy_number":20,"expression_load":.5}
def test_exact_seeded_wright_fisher_simulation_is_reproducible():
 a=stochastic_drift(construct(),generations=30,population=1000,replicates=16,seed=2); b=stochastic_drift(construct(),generations=30,population=1000,replicates=16,seed=2); assert a==b and len(a["terminal_fractions"])==16 and "Wright-Fisher" in a["model_status"]
def test_high_burden_is_less_stable():
 a=stochastic_drift({**construct(),"burden":.1},generations=30,population=1000,replicates=32); b=stochastic_drift({**construct(),"burden":.9},generations=30,population=1000,replicates=32); assert a["terminal_mean"]>b["terminal_mean"]
def test_intervention_ranking_has_live_alternatives():
 r=optimize_stability(construct(),generations=100); assert len(r["ranking"])==5 and r["ranking"][0]["stability_score"]>r["ranking"][-1]["stability_score"]
def test_exactly_fifty_case_derived_diagnostics():
 r=analyze_stability(construct(),generations=30,population=1000,replicates=16); assert len(r["diagnostics"])==50 and len(set(r["diagnostics"]))==50
def test_end_to_end_is_actionable_and_honest():
 r=analyze_stability(construct(),generations=20,population=1000,replicates=8); assert r["diagnostic_count"]==50 and r["failure_modes"] and len(r["validation_plan"])==4 and "no production-lot prediction" in r["simulation"]["model_status"]
def test_legacy_forecast_remains_available(): assert stability_forecast(construct(),20)["trajectory"]
def test_validation_errors_are_informative():
 with pytest.raises(ValueError,match="burden"): validate_construct({"burden":2,"size_kb":1})
 with pytest.raises(ValueError,match="size_kb"): validate_construct({"burden":.2,"size_kb":0})
 with pytest.raises(ValueError,match="replicates"): stochastic_drift(construct(),replicates=1)

def test_v2_sequence_risk_map_and_distinct_mutation_modes():
 from sugarcode.modules.stability_ai.core import analyze_stability_v2
 c={**construct(),"sequence":"GCGCGCGCGC"+"AAAAAAAAAA"+"ATGC"*20,"protein_sequence":"M"*100}
 r=analyze_stability_v2(c,generations=10,population=500,replicates=8)
 assert r["sequence_risk_map"]["regions"] and r["mutation_risk_map"]["point"]!=r["mutation_risk_map"]["insertion"]!=r["mutation_risk_map"]["deletion"]
 assert "vulnerable_regions" in r["mutation_risk_map"]

def test_v2_copy_number_environment_and_biochemical_layers_are_live():
 from sugarcode.modules.stability_ai.core import analyze_stability_v2
 c={**construct(),"sequence":"ATGC"*30,"protein_sequence":"MKT"*40}
 mild=analyze_stability_v2(c,environment={"temperature_C":30,"pH":7,"oxidative_stress":0},generations=10,population=500,replicates=8)
 harsh=analyze_stability_v2(c,environment={"temperature_C":45,"pH":5,"oxidative_stress":.8},generations=10,population=500,replicates=8)
 assert mild["molecular_profile"]["environmental_stress_index"]<harsh["molecular_profile"]["environmental_stress_index"]
 assert mild["simulation"]["trajectory"][-1]["functional_mean"]>harsh["simulation"]["trajectory"][-1]["functional_mean"]
 assert "copy_number_mean" in mild["simulation"]["trajectory"][-1] and "protein" in mild["molecular_profile"] and "biochemical" in mild["molecular_profile"]
 assert {"sequence_redundancy","kill_switch","selection_pressure"}<= {x["intervention"] for x in mild["interventions"]["ranking"]}

def test_canonical_end_to_end_v3_has_fifty_full_stack_environment_sensitive_diagnostics():
 c={**construct(),"sequence":"GCGC"*15+"AAAAAAAAAA"+"ATGC"*20,"protein_sequence":"MKT"*40}
 mild=analyze_stability(c,environment={"temperature_C":30,"pH":7,"oxidative_stress":0},generations=12,population=500,replicates=8,seed=5)
 harsh=analyze_stability(c,environment={"temperature_C":48,"pH":5,"oxidative_stress":.9},generations=12,population=500,replicates=8,seed=5)
 assert mild["diagnostic_count"]==50 and len(mild["diagnostics"])==50 and len(set(mild["diagnostics"]))==50
 assert {"sequence_risk_max","point_mutation_rate","insertion_rate","deletion_rate","terminal_copy_number_mean","aggregation_probability","metabolite_24h_survival"} <= set(mild["diagnostics"])
 assert sum(mild["diagnostics"][k]!=harsh["diagnostics"][k] for k in mild["diagnostics"])>=15
 assert mild["diagnostics"]["terminal_functional_mean"]>harsh["diagnostics"]["terminal_functional_mean"]
