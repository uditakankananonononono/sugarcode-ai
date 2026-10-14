"""Unit 43 v9: tests-only pins for core.py survivors of an independent AST sweep (PARTIAL; interim, sweep still running).

Hand-literal oracles. linprog / pfba are stubbed so each test isolates one line.
 - L115 pfba stage-2 floor = raw_optimum * optimum_fraction - 1e-9 (0.8 * 0.5 - 1e-9 = 0.4 - 1e-9)
 - L125 pfba fallback message "failed: <message>" and method "fba"
 - L127 pfba fluxes carry no negative zero (-0.0 -> 0.0)
 - L151 rerouting: strict > 1e-6 (diff exactly 1e-6 excluded, 0.5 included); knocked-out reaction excluded
"""
import math
import numpy as np

from sugarcode.modules.virtual_cell import core
from sugarcode.modules.virtual_cell.core import MetabolicModel


class _R:
    def __init__(self, x=None, fun=0.0, ok=True, msg="stub"):
        self.success, self.x, self.fun, self.message = ok, (None if x is None else np.array(x, float)), fun, msg


def _model():
    # one metabolite, A_up -> A (+1), BIO consumes A (-1)
    return MetabolicModel(["A"], ["UP", "BIO"], [[1.0, -1.0]], [0.0, 0.0], [10.0, 10.0], "BIO")


def _stub(monkeypatch, results):
    calls = []
    it = iter(results)

    def fake(c, **kw):
        calls.append(kw)
        return next(it)
    monkeypatch.setattr(core, "linprog", fake)
    return calls


def test_pfba_stage2_floor_exact(monkeypatch):
    # stage 1: optimum 0.8 (fun -0.8); stage 2 returns x = [0.4,0.4 | 0,0]
    calls = _stub(monkeypatch, [_R([0.8, 0.8], -0.8), _R([0.4, 0.4, 0.0, 0.0], 0.8)])
    core.pfba(_model(), optimum_fraction=0.5)
    b = calls[1]["bounds"]  # [(lo,hi) pos parts] + [neg parts]; BIO is index 1
    assert b[1][0] == (0.8 * 0.5 - 1e-9)
    assert b[1][0] != 0.8 / 0.5 - 1e-9 and b[1][0] != 0.8 * 0.5 + 1e-9


def test_pfba_failure_message_exact(monkeypatch):
    _stub(monkeypatch, [_R([1.0, 1.0], -1.0), _R(ok=False, msg="boom")])
    out = core.pfba(_model())
    assert out["method"] == "fba"
    assert out["pfba_stage"] == "failed: boom"
    assert out["status"] == "optimal" and out["objective"] == 1.0


def test_pfba_no_negative_zero_flux(monkeypatch):
    _stub(monkeypatch, [_R([1.0, 1.0], -1.0), _R([1.0, -0.0, 0.0, 0.0], 1.0)])
    out = core.pfba(_model())
    assert out["fluxes"]["BIO"] == 0.0 and math.copysign(1.0, out["fluxes"]["BIO"]) == 1.0
    assert out["fluxes"]["UP"] == 1.0


def test_knockout_rerouting_threshold_and_exclusion(monkeypatch):
    m = MetabolicModel(["A"], ["K", "X", "Y", "Z"], [[1.0, -1.0, 0.0, 0.0]], [0] * 4, [10] * 4, "X")

    def fake_pfba(model, objective=None, bounds_override=None):
        if bounds_override:  # knockout of K: K moves by 5 (must be excluded), X unchanged, Y +1e-6 exactly (excluded), Z +0.5
            return {"objective": 1.0, "fluxes": {"K": 0.0, "X": 1.0, "Y": 1e-6, "Z": 0.5}}
        return {"objective": 1.0, "fluxes": {"K": 5.0, "X": 1.0, "Y": 0.0, "Z": 0.0}}
    monkeypatch.setattr(core, "pfba", fake_pfba)
    out = core.gene_knockout(m, "K")
    assert out["lethality"] == "viable"
    assert out["rerouting"] == {"Z": 0.5}
