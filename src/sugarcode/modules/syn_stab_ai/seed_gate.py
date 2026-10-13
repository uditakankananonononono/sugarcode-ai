"""Explicit-import seed gates only; legacy entry points remain unchanged."""
from . import core
from ...seed_check import check_seed

def population_simulation(initial_functional=1, mutation_rate=0.001, selection_cost=0.01, drift_population=1000, generations=100, seed=0):
    seed=check_seed(seed)
    return core.population_simulation(initial_functional,mutation_rate,selection_cost,drift_population,generations,seed)
