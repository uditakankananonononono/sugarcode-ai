"""Explicit-import seed gates only; legacy entry points remain unchanged."""
from . import core
from ...seed_check import check_seed

def evolve(pathway_genes=None, generations=2000, pop_size=500, mutation_rate=0.001, burden_cost=0.08, selection_on_yield=0.5, seed=42, sample_every=100):
    seed=check_seed(seed)
    return core.evolve(pathway_genes,generations,pop_size,mutation_rate,burden_cost,selection_on_yield,seed,sample_every)

def simulate_evolution_experiment(genes, *, generations=2000, population=5000, burden=0.08, yield_selection=0.5, mutation_rate=0.0001, environment_schedule=None, sample_every=50, seed=42):
    seed=check_seed(seed)
    return core.simulate_evolution_experiment(genes,generations=generations,population=population,burden=burden,yield_selection=yield_selection,mutation_rate=mutation_rate,environment_schedule=environment_schedule,sample_every=sample_every,seed=seed)

def simulate_competition(genes, *, generations=2000, population=5000, burden=0.08, yield_selection=0.5, mutation_rate=0.0001, competitor_name='wild-type competitor', competitor_fraction=0.01, competitor_fitness=1.0, environment_schedule=None, sample_every=50, seed=42):
    seed=check_seed(seed)
    return core.simulate_competition(genes,generations=generations,population=population,burden=burden,yield_selection=yield_selection,mutation_rate=mutation_rate,competitor_name=competitor_name,competitor_fraction=competitor_fraction,competitor_fitness=competitor_fitness,environment_schedule=environment_schedule,sample_every=sample_every,seed=seed)
