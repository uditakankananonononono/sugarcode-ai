"""Verified named functions; other entries excluded by scope.

Explicit-import seed gates only; legacy entry points remain unchanged.
"""
from . import core as core
from ...seed_check import check_seed

def _ci(values, statistic, seed, samples=400):
    seed=check_seed(seed)
    return core._ci(values,statistic,seed,samples)

def evaluate_library(smiles, *, reference_smiles=None, n_bits=256, seed=29, max_pairs=10000):
    seed=check_seed(seed)
    return core.evaluate_library(smiles,reference_smiles=reference_smiles,n_bits=n_bits,seed=seed,max_pairs=max_pairs)

def compare_libraries(generated, reference, *, n_bits=256, seed=29):
    seed=check_seed(seed)
    return core.compare_libraries(generated,reference,n_bits=n_bits,seed=seed)
