import numpy as np
import pytest
from sugarcode.modules.synlife_evo import simulate_evolution_experiment,optimize_stability
def test_product_api_actionable_and_normalized():
 r=simulate_evolution_experiment(["A","B"],generations=100,population=500,sample_every=10); assert np.isclose(sum(r["final_genotype_frequencies"].values()),1); assert r["recommended_next_steps"] and r["experiment"]["mutation_rate_per_gene_generation"]>0
def test_environment_schedule_changes_are_recorded():
 s=[{"start":0,"end":50,"name":"growth","product_selection":0},{"start":50,"end":101,"name":"production","product_selection":1}]; r=simulate_evolution_experiment(["A"],generations=100,population=500,sample_every=10,environment_schedule=s); assert r["diagnostics"]["environment_transition_count"]==1
def test_seeded_reproducibility():
 a=simulate_evolution_experiment(["A"],generations=50,population=200,sample_every=10,seed=3); b=simulate_evolution_experiment(["A"],generations=50,population=200,sample_every=10,seed=3); assert a==b
def test_50_computed_diagnostics_disclaimer_separate():
 r=simulate_evolution_experiment(["A","B"],generations=100,population=500,sample_every=10); assert len(r["diagnostics"])>=50 and "model_status" not in r["diagnostics"] and "not trained" in r["model_status"]
def test_informative_validation():
 with pytest.raises(ValueError,match="unique"): simulate_evolution_experiment(["A","A"])
 with pytest.raises(ValueError,match="population"): simulate_evolution_experiment(["A"],population=10)
 with pytest.raises(ValueError,match="mutation_rate"): simulate_evolution_experiment(["A"],mutation_rate=-1)
def test_stability_optimizer_returns_direct_experimental_parameters():
 r=optimize_stability(["A"],generations=50,population=200); assert .005<=r["recommended_burden_per_gene"]<=.15 and .05<=r["recommended_product_selection"]<=1
