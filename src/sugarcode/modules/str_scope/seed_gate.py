"""Explicit-import seed gates only; legacy entry points remain unchanged."""
from . import core
from ...seed_check import check_seed

def repeat_instability(initial_repeats, divisions=50, slippage=0.05, mmr=0.8, ber=0.5, seed=0, trajectories=500):
    seed=check_seed(seed)
    return core.repeat_instability(initial_repeats,divisions,slippage,mmr,ber,seed,trajectories)
