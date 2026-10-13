"""Seed validation in front of core functions that pass `seed` to numpy default_rng.

numpy.random.default_rng crashes the interpreter (SIGSEGV) on a deeply nested list seed, so the
seed is checked before core runs by the shared helper (int or numpy integer, not bool, 0..2**63-1). Nothing else is validated or changed;
all other arguments are passed to core untouched.
"""
from __future__ import annotations

import functools
import inspect

from . import core

from sugarcode.seed_check import MAX_SEED, check_seed  # noqa: F401  (shared helper, 0..2**63-1)


def _guard(fn):
    sig = inspect.signature(fn)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        if "seed" in bound.arguments:
            bound.arguments["seed"] = check_seed(bound.arguments["seed"])
        return fn(*bound.args, **bound.kwargs)

    return wrapper


mechanistic_cell_program = _guard(core.mechanistic_cell_program)
design_syndroid = _guard(core.design_syndroid)
