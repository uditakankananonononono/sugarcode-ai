"""Shared seed check for code that hands a seed to numpy.random.default_rng.

default_rng crashes the interpreter (SIGSEGV, exit 139) on a deeply nested list seed, so the seed
is checked before it gets there: an int or a numpy integer (not bool), 0..MAX_SEED. None is accepted
only when the caller says its core allows it. Returns the seed as a plain int (None stays None).
"""
from __future__ import annotations

import numpy as np

MAX_SEED = 2**63 - 1


def check_seed(seed, *, allow_none: bool = False):
    if seed is None and allow_none:
        return None
    if isinstance(seed, (bool, np.bool_)) or not isinstance(seed, (int, np.integer)):
        raise TypeError("seed must be an integer")
    value = int(seed)
    if not 0 <= value <= MAX_SEED:
        raise ValueError(f"seed must be between 0 and {MAX_SEED}")
    return value
