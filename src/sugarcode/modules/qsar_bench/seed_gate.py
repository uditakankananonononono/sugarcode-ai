"""Verified named functions; other entries excluded by scope.

Explicit-import seed gates only; legacy entry points remain unchanged.
"""
from . import model as core
from ...seed_check import check_seed

def _split_indices(smiles, strategy, fraction, seed, years=None):
    seed=check_seed(seed)
    return core._split_indices(smiles,strategy,fraction,seed,years)

def validate_qsar(smiles, y, *, strategy='scaffold', test_fraction=0.2, seed=17, years=None, alpha=1.0, n_bits=256):
    seed=check_seed(seed)
    return core.validate_qsar(smiles,y,strategy=strategy,test_fraction=test_fraction,seed=seed,years=years,alpha=alpha,n_bits=n_bits)
