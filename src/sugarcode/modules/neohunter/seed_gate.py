"""Explicit-import seed gates only; legacy entry points remain unchanged."""
from . import core as core
from ...seed_check import check_seed

def simulate_immune_escape(candidates, generations=100, population=10000, seed=13):
    seed=check_seed(seed)
    return core.simulate_immune_escape(candidates,generations,population,seed)
