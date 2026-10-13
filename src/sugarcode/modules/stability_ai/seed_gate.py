"""Explicit-import seed gates only; legacy entry points remain unchanged."""
from . import core
from ...seed_check import check_seed

def stochastic_drift(construct, *, generations=200, population=10000, replicates=64, seed=42):
    seed=check_seed(seed)
    return core.stochastic_drift(construct,generations=generations,population=population,replicates=replicates,seed=seed)

def stochastic_drift_v2(construct, *, environment=None, generations=200, population=10000, replicates=64, seed=42):
    seed=check_seed(seed)
    return core.stochastic_drift_v2(construct,environment=environment,generations=generations,population=population,replicates=replicates,seed=seed)
