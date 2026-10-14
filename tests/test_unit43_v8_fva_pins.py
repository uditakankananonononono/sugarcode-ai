"""Unit 43 v8: tests-only pin for the last fva survivor of an independent AST sweep (PARTIAL).

Survivor: the scale constant 1.0 in the fallback relaxation 1e-9 * max(1.0, |optimum|). The fallback LP bound is only
used when the exact-floor LP fails, so linprog is stubbed. Hand literals: optimum 0.5, fraction 1.0 -> bound 0.5, relaxed
floor 0.5 - 1e-9 * max(1.0, 0.5) = 0.5 - 1e-9 (scale 1.0, since |optimum| < 1); optimum 4.0 -> 4.0 - 4e-9.
"""
import types

import numpy as np
import pytest

from sugarcode.modules.virtual_cell import fva


def _model(ub):
    return types.SimpleNamespace(S=[[0.0]], lb=[0.0], ub=[ub], reactions=["r"], metabolites=["m"], objective="r")


class _R:
    def __init__(self, x, ok=True):
        self.success = ok
        self.x = np.array([x])
        self.fun = -x
        self.message = "stub"


def _run(monkeypatch, opt):
    script = iter([_R(opt), _R(opt, ok=False), _R(opt), _R(opt)])
    seen = []

    def fake(c, A_eq=None, b_eq=None, bounds=None, method=None):
        seen.append([tuple(b) for b in bounds])
        return next(script)
    monkeypatch.setattr(fva, "linprog", fake)
    out = fva.flux_variability(_model(opt))
    return out, seen


def test_fallback_floor_uses_scale_one_when_optimum_below_one(monkeypatch):
    out, seen = _run(monkeypatch, 0.5)
    assert out["objective_bound"] == 0.5
    assert seen[1][0][0] == 0.5          # exact floor tried first
    assert seen[2][0][0] == 0.5 - 1e-9   # relaxed floor: scale max(1.0, 0.5) == 1.0
    assert seen[3][0][0] == 0.5          # second sign uses the exact floor again


def test_fallback_floor_scales_with_optimum_when_above_one(monkeypatch):
    out, seen = _run(monkeypatch, 4.0)
    assert seen[1][0][0] == 4.0
    assert seen[2][0][0] == 4.0 - 4e-9
