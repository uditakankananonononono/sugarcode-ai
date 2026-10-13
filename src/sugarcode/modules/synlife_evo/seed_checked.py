"""Seed-checked entry points for synlife_evo functions that pass `seed` to random.Random.

Only the seed is checked (shared helper: int or numpy integer, not bool, 0..2**63-1); every other argument goes to core unchanged.
Design generators are out of scope and not wrapped.
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


evolve = _guard(core.evolve)
simulate_evolution_experiment = _guard(core.simulate_evolution_experiment)
optimize_stability = _guard(core.optimize_stability)
simulate_competition = _guard(core.simulate_competition)
