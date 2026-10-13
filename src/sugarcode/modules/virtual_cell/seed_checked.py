"""Seed-checked entry points for virtual_cell functions that pass `seed` to random.Random.

Only the seed is checked (shared helper: int or numpy integer, not bool, 0..2**63-1); every other argument goes to core unchanged.
Core crash (nested-list seed) happens only with method='gillespie' (random.Random path). With the default method='ode' core ignores the seed.
Behavior change: the gate checks the seed regardless of method, so an invalid seed (bool, float, out of range, ...) that the 'ode' path used to accept silently is now refused.
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


simulate_expression = _guard(core.simulate_expression)
simulate_cell = _guard(core.simulate_cell)
