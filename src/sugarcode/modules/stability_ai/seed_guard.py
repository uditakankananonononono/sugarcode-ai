"""Seed validation in front of core functions that pass `seed` to numpy default_rng.

numpy.random.default_rng crashes the interpreter (SIGSEGV) on a deeply nested list seed, so the
seed is checked before core runs: an int (not bool) in 0..MAX_SEED. Nothing else is validated or changed;
all other arguments are passed to core untouched.
"""
from __future__ import annotations

import functools
import inspect

from . import core

MAX_SEED = 2**32 - 1


def check_seed(seed):
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")
    if not 0 <= seed <= MAX_SEED:
        raise ValueError(f"seed must be between 0 and {MAX_SEED}")
    return seed


def _guard(fn):
    sig = inspect.signature(fn)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        if "seed" in bound.arguments:
            check_seed(bound.arguments["seed"])
        return fn(*args, **kwargs)

    return wrapper


stochastic_drift = _guard(core.stochastic_drift)
stochastic_drift_v2 = _guard(core.stochastic_drift_v2)
analyze_stability = _guard(core.analyze_stability)
analyze_stability_v2 = _guard(core.analyze_stability_v2)
