"""Positional-argument pins for seed_checked_study (PARTIAL). A spy with core's exact signature records
what the wrapper forwards, so reordered or dropped positionals are caught. Expected values are the literals passed in."""
import functools
import importlib
import inspect

import numpy as np

PKG = "sugarcode.modules.neuro_pipeline"
core = importlib.import_module(PKG + ".core")
sc = importlib.import_module(PKG + ".seed_checked_study")
MODEL = core.train(epochs=3)["model"]


def spied(core_fn):
    seen = []

    @functools.wraps(core_fn)  # inspect.signature follows __wrapped__, so the spy has core's signature
    def spy(*a, **k):
        b = inspect.signature(core_fn).bind(*a, **k)
        seen.append(dict(b.arguments))
        return "sentinel"

    return sc._guard(spy), seen


def test_rsa_positional_call_forwards_n_in_n_stimuli_seed():
    w, seen = spied(core.rsa)
    assert w(MODEL, 8, 5, 3) == "sentinel"
    assert len(seen) == 1
    assert seen[0] == {"model": MODEL, "n_in": 8, "n_stimuli": 5, "seed": 3}
    assert seen[0]["model"] is MODEL


def test_lesion_study_positional_call_forwards_n_in_seed():
    w, seen = spied(core.lesion_study)
    assert w(MODEL, 8, 3) == "sentinel"
    assert len(seen) == 1
    assert seen[0] == {"model": MODEL, "n_in": 8, "seed": 3}
    assert seen[0]["model"] is MODEL


def test_numpy_integer_positional_seed_is_checked_and_forwarded_as_given_value():
    w, seen = spied(core.rsa)
    w(MODEL, 8, 5, np.int64(3))
    assert seen[0]["seed"] == 3 and seen[0]["n_stimuli"] == 5
    assert type(seen[0]["seed"]) is int  # check_seed returns a plain int


def test_real_wrapper_positional_equals_core_positional():
    # n_in=6 is the trained model input width (8 raises a matmul mismatch in core)
    for fn, args in (("rsa", (MODEL, 6, 5, 3)), ("lesion_study", (MODEL, 6, 3))):
        a = repr(getattr(sc, fn)(*args))
        b = repr(getattr(core, fn)(*args))
        assert a == b, fn


def test_positional_seed_is_refused_and_core_not_called():
    import pytest
    cap = 2**63 - 1
    for fn, pre in (("rsa", (MODEL, 8, 5)), ("lesion_study", (MODEL, 8))):
        w, seen = spied(getattr(core, fn))
        for bad in (True, 1.0, "1", None):
            with pytest.raises(TypeError, match="seed must be an integer"):
                w(*pre, bad)
        for bad in (-1, cap + 1):
            with pytest.raises(ValueError, match="seed must be between 0 and"):
                w(*pre, bad)
        assert seen == []
