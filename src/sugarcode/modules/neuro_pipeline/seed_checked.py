"""Seed-checked entry points for neuro_pipeline functions that pass `seed` to numpy.random.default_rng.

Only the seed is checked (shared helper: int or numpy integer, not bool, 0..2**63-1); every other argument goes to core unchanged.
A nested-list seed crashes the interpreter in core (rc -11, checked for all 3 wrapped functions on 3.10); the gate refuses it first.
Functions already wrapped by seed_gate.py are not wrapped here.
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


synthetic_promoter_dataset = _guard(core.synthetic_promoter_dataset)
sequence_pipeline_demo = _guard(core.sequence_pipeline_demo)
train_on_sequences = _guard(core.train_on_sequences)
