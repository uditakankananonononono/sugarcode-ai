"""Explicit-import seed gates only; legacy entry points remain unchanged."""
from . import model as core
from ...seed_check import check_seed

def _split_indices(smiles, strategy, fraction, seed, years=None):
    seed=check_seed(seed)
    return core._split_indices(smiles,strategy,fraction,seed,years)
