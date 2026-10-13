"""Seed-checked entry points for the two syndroid core functions that take a seed straight from the caller."""
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


stochastic_gene_expression = _guard(core.stochastic_gene_expression)
evolutionary_stability = _guard(core.evolutionary_stability)
