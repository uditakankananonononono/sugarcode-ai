"""Unit 43 v5: tests-only pins for fva survivors (PARTIAL). Hand literals, linprog stubbed."""
import types
import numpy as np
import pytest
from sugarcode.modules.virtual_cell import fva


def _model(ub=10.0):
    return types.SimpleNamespace(S=[[0.0]], lb=[0.0], ub=[ub], reactions=["r"],
                                 metabolites=["m"], objective="r")


class _R:
    def __init__(self, x, ok=True):
        self.success = ok; self.x = np.array([x]); self.fun = -x; self.message = "stub"


def _stub(monkeypatch, script, seen=None):
    it = iter(script)

    def fake(c, A_eq=None, b_eq=None, bounds=None, method=None):
        if seen is not None:
            seen.append(list(bounds))
        return next(it)
    monkeypatch.setattr(fva, "linprog", fake)


def test_default_tol_is_exactly_1e_minus_6(monkeypatch):
    _stub(monkeypatch, [_R(1.0), _R(1.0), _R(1.0 + 0.999e-6)])
    assert fva.flux_variability(_model())["ranges"]["r"]["fixed"] is True
    _stub(monkeypatch, [_R(1.0), _R(1.0), _R(1.0 + 1.001e-6)])
    assert fva.flux_variability(_model())["ranges"]["r"]["fixed"] is False
    sig = fva.flux_variability.__defaults__
    assert sig[-1] == 1e-6


def test_fraction_slightly_below_zero_refused():
    with pytest.raises(ValueError, match="fraction_of_optimum must be in"):
        fva.flux_variability(_model(), fraction_of_optimum=-1e-12)
    with pytest.raises(ValueError, match="fraction_of_optimum must be in"):
        fva.flux_variability(_model(), fraction_of_optimum=1.0 + 1e-12)


def test_infinite_upper_bound_refused():
    with pytest.raises(ValueError, match="upper bound must be finite"):
        fva.flux_variability(_model(), bounds_override={"r": (0.0, float("inf"))})
    with pytest.raises(ValueError, match="lower bound must be finite"):
        fva.flux_variability(_model(), bounds_override={"r": (float("-inf"), 1.0)})
    with pytest.raises(ValueError, match="finite vectors"):
        fva.flux_variability(_model(ub=float("inf")))


@pytest.mark.parametrize("opt,expected_lb", [(0.5, 0.5 - 1e-9), (100.0, 100.0 - 1e-7)])
def test_fallback_slack_scale_is_max_one_abs_opt(monkeypatch, opt, expected_lb):
    seen = []
    # base ok; exact-floor LP fails; fallback LP succeeds; then max LP ok (exact)
    _stub(monkeypatch, [_R(opt), _R(0, ok=False), _R(opt), _R(opt)], seen)
    r = fva.flux_variability(_model(ub=1000.0))
    assert r["ranges"]["r"]["min"] == opt
    exact_lb = seen[1][0][0]
    fallback_lb = seen[2][0][0]
    assert exact_lb == opt
    assert fallback_lb == pytest.approx(expected_lb, abs=1e-13)
    assert abs(fallback_lb - expected_lb) < 1e-13


def test_tol_zero_fixed_only_when_bit_identical(monkeypatch):
    _stub(monkeypatch, [_R(3.0), _R(3.0), _R(3.0)])
    assert fva.flux_variability(_model(), tol=0)["ranges"]["r"]["fixed"] is True
    _stub(monkeypatch, [_R(3.0), _R(3.0), _R(3.0 + 4.4e-16)])
    assert fva.flux_variability(_model(), tol=0)["ranges"]["r"]["fixed"] is False
    doc = fva.__doc__
    assert "tol=0" in doc and "bit-for-bit identical" in doc and "fixed=False" in doc


@pytest.mark.parametrize("f", [0.0, 1.0, 0.5])
def test_fraction_edges_accepted(monkeypatch, f):
    _stub(monkeypatch, [_R(4.0), _R(4.0), _R(4.0)])
    r = fva.flux_variability(_model(), fraction_of_optimum=f)
    assert r["fraction_of_optimum"] == f
    assert r["objective_bound"] == 4.0 * f
