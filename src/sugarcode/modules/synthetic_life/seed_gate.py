"""Explicit-import seed gates only; legacy entry points remain unchanged."""
from . import core
from ...seed_check import check_seed

def stochastic_control(hours=12, dt=0.05, seed=0, transcription=0.5, translation=1, degradation=0.2):
    seed=check_seed(seed)
    return core.stochastic_control(hours,dt,seed,transcription,translation,degradation)

def ale_trajectory(generations=500, initial_fitness=1, mutation_supply=0.02, selection=0.05, seed=0):
    seed=check_seed(seed)
    return core.ale_trajectory(generations,initial_fitness,mutation_supply,selection,seed)
