"""Behavior pins for the seed handling of stability_ai.stochastic_drift and stochastic_drift_v2.

The module under test is the first of seed_gate / seed_guard that exists, so the same pins hold
whichever one the package keeps after the duplicate wrapper is removed.
"""
import importlib
import re
import subprocess
import sys

import numpy as np
import pytest

BASE = "sugarcode.modules.stability_ai"


def load_gate():
    for name in ("seed_gate", "seed_guard"):
        try:
            return importlib.import_module(f"{BASE}.{name}")
        except ModuleNotFoundError as e:
            if e.name != f"{BASE}.{name}":
                raise
    raise AssertionError("no seed_gate or seed_guard module in stability_ai")


gate = load_gate()
core = importlib.import_module(f"{BASE}.core")
CAP = 2**63 - 1
STAB = {"mode": "plasmid", "burden": 0.1, "size_kb": 5}
KW = dict(generations=5, population=50, replicates=4)
FUNCS = ["stochastic_drift", "stochastic_drift_v2"]


def msg(s):
    return re.escape(s) + "$"


@pytest.mark.parametrize("fn", FUNCS)
def test_bad_seed_type_message(fn):
    for bad in (True, False, np.bool_(True), 1.0, "1", None, [1], [[]], 1 + 0j):
        with pytest.raises(TypeError, match=msg("seed must be an integer")):
            getattr(gate, fn)(STAB, seed=bad, **KW)


@pytest.mark.parametrize("fn", FUNCS)
def test_bad_seed_range_message_and_cap_boundary(fn):
    for bad in (-1, CAP + 1, 2**64, -(2**64), 10**400):
        with pytest.raises(ValueError, match=msg(f"seed must be between 0 and {CAP}")):
            getattr(gate, fn)(STAB, seed=bad, **KW)
    for ok in (0, CAP):
        assert getattr(gate, fn)(STAB, seed=ok, **KW) == getattr(core, fn)(STAB, seed=ok, **KW)


@pytest.mark.parametrize("fn", FUNCS)
def test_numpy_int_seed_and_default_seed_match_core(fn):
    g, c = getattr(gate, fn), getattr(core, fn)
    assert g(STAB, seed=np.int64(7), **KW) == c(STAB, seed=7, **KW)
    assert g(STAB, seed=np.uint8(7), **KW) == c(STAB, seed=7, **KW)
    assert g(STAB, **KW) == c(STAB, **KW)


@pytest.mark.parametrize("fn", FUNCS)
def test_seed_checked_before_core_validation(fn):
    # a bad seed wins over a bad burden: the seed is refused first
    bad = {"mode": "plasmid", "burden": 5, "size_kb": 5}
    with pytest.raises(TypeError, match=msg("seed must be an integer")):
        getattr(gate, fn)(bad, seed=True, **KW)
    with pytest.raises(ValueError, match=msg("burden must be in [0, 1]")):
        getattr(gate, fn)(bad, seed=1, **KW)


@pytest.mark.parametrize("fn", FUNCS)
def test_deep_list_seed_is_refused_not_crashed(fn):
    body = ("import sys; sys.setrecursionlimit(10**7); s = []\nfor _ in range(100000): s = [s]\n"
            f"from {BASE} import {gate.__name__.rsplit('.', 1)[1]} as m\n"
            f"m.{fn}({STAB!r}, seed=s)\n")
    r = subprocess.run([sys.executable, "-c", body], capture_output=True, text=True, timeout=120)
    assert r.returncode == 1
    assert r.stderr.strip().splitlines()[-1] == "TypeError: seed must be an integer"
