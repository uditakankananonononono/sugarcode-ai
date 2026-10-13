"""Seed-checked entry points for bioprint_pro functions that pass `seed` to numpy default_rng.

Only the seed is checked (shared helper: int or numpy integer, not bool, 0..2**63-1); every other argument goes to core unchanged.
"""
from __future__ import annotations

import functools
import inspect

from sugarcode.seed_check import check_seed

from . import core


def _guard(fn):
    sig = inspect.signature(fn)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        if "seed" in bound.arguments:
            bound.arguments["seed"] = check_seed(bound.arguments["seed"])
        return fn(*bound.args, **bound.kwargs)

    return wrapper


oldroyd_b_extrusion = _guard(core.oldroyd_b_extrusion)
optimize_print = _guard(core.optimize_print)
