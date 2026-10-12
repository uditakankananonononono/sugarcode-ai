"""Simulation metadata completeness; no empirical provenance certification."""
from sugarcode.modules.synlife_evo import simulate_evolution_experiment


def test_experiment_records_operator_parameters_and_origin():
    out = simulate_evolution_experiment(['G'], generations=20, population=100,
        burden=.04, yield_selection=.7, mutation_rate=.001, sample_every=5, seed=9)
    exp = out['experiment']
    assert exp['burden_per_gene'] == .04
    assert exp['yield_selection'] == .7
    assert exp['sample_every_generations'] == 5
    assert exp['parameter_origin'] == 'function arguments; external provenance not checked'
    assert exp['seed'] == 9
    assert exp['mutation_rate_per_gene_generation'] == .001
