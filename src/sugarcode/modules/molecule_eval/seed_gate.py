"""Explicit-import seed gates only; legacy entry points remain unchanged."""
from . import core as core
from ...seed_check import check_seed

def _ci(values, statistic, seed, samples=400):
    seed=check_seed(seed)
    return core._ci(values,statistic,seed,samples)
