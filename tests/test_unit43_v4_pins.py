"""Unit 43 v4 (PARTIAL): pins for fva.flux_variability. Expected values are hand-derived literals (binary fractions,
exact in float). Covers (a) the relaxation-leak defect: the objective floor must be exact, so reported min/max are the
true bounds; (b) survivors L21 L26 L71 L75 L82 L83 reported by lane 7. Test-only on top of the fva.py fix: red against
the pre-fix fva.py and against single-line mutants, green on the fixed code."""
import numpy as np
import pytest
from sugarcode.modules.virtual_cell import fva as fvamod
from sugarcode.modules.virtual_cell.core import MetabolicModel
from sugarcode.modules.virtual_cell.fva import flux_variability as FVA

REAL = fvamod.linprog


def chain(u):  # IN -> A -> OUT ; v_IN = v_OUT, objective OUT in [0,u]
    return MetabolicModel(["A"], ["IN", "OUT"], np.array([[1., -1.]]), np.array([0., 0.]), np.array([u, 1e12]), "OUT")


@pytest.mark.parametrize("u,kw", [(10, {"tol": 0}), (0.5, {"tol": 0}), (0.25, {"tol": 0}), (1e9, {}), (1e9, {"tol": 0})])
def test_fixed_reaction_reports_true_bounds(u, kw):
    r = FVA(chain(u), **kw)
    assert r["optimum"] == float(u)
    for n in ("IN", "OUT"):
        assert r["ranges"][n] == {"min": float(u), "max": float(u), "fixed": True, "blocked": False}


def test_fraction_floor_exact_values():
    # OUT in [0.5*10, 10] at fraction 0.5: floor is exactly 5, not 5-1e-8
    r = FVA(chain(10), fraction_of_optimum=0.5, tol=0)
    assert r["objective_bound"] == 5.0
    assert r["ranges"]["OUT"]["min"] == 5.0 and r["ranges"]["OUT"]["max"] == 10.0 and r["ranges"]["OUT"]["fixed"] is False


def free_model():  # dummy objective D (no stoichiometry) plus free reversible IN<->OUT through A
    S = np.array([[1., -1., 0.]])
    return MetabolicModel(["A"], ["IN", "OUT", "D"], S, np.array([-1., -1., 0.]), np.array([1., 1., 1.]), "D")


def test_tie_boundaries_exact():
    m = free_model()
    r = FVA(m, bounds_override={"IN": (-0.5, 0.25), "OUT": (-0.5, 0.25)}, tol=0.5)["ranges"]["IN"]
    assert (r["min"], r["max"]) == (-0.5, 0.25) and r["blocked"] is True      # |lo| == tol (L83)
    r = FVA(m, bounds_override={"IN": (-0.25, 0.5), "OUT": (-0.25, 0.5)}, tol=0.5)["ranges"]["IN"]
    assert (r["min"], r["max"]) == (-0.25, 0.5) and r["blocked"] is True      # |hi| == tol
    r = FVA(m, bounds_override={"IN": (-0.5, 0.5), "OUT": (-0.5, 0.5)}, tol=1.0)["ranges"]["IN"]
    assert r["fixed"] is True                                                  # hi-lo == tol (L82)
    r = FVA(m, bounds_override={"IN": (-0.5, 0.5), "OUT": (-0.5, 0.5)}, tol=0.5)["ranges"]["IN"]
    assert r["fixed"] is False and r["blocked"] is True


def test_default_tol_is_1e_minus_6():
    m = free_model()
    narrow = FVA(m, bounds_override={"IN": (0, 5e-7), "OUT": (0, 5e-7)})["ranges"]["IN"]
    wide = FVA(m, bounds_override={"IN": (0, 2e-6), "OUT": (0, 2e-6)})["ranges"]["IN"]
    unit = FVA(m, bounds_override={"IN": (0, 1), "OUT": (0, 1)})["ranges"]["IN"]
    assert narrow["fixed"] is True and narrow["blocked"] is True
    assert wide["fixed"] is False and wide["blocked"] is False
    assert unit["fixed"] is False


def test_tol_cap_edge_1e12():
    FVA(chain(1), tol=1e12)
    with pytest.raises(ValueError):
        FVA(chain(1), tol=1e12 + 1.0)
    with pytest.raises(ValueError):
        FVA(chain(1), tol=float(1e12 + 1.0))


@pytest.mark.parametrize("u", [10.0, 0.5, 1e9])
def test_fallback_slack_and_sign_vectors(u, monkeypatch):
    # force the exact-floor LP to "fail" so the documented fallback relaxation 1e-9*max(1,|opt|) is exercised
    calls = []
    first = {"n": 0}
    def fake(c, **kw):
        lbs = np.array([b[0] for b in kw["bounds"]])
        calls.append((np.array(c), lbs))
        if first["n"] == 0:      # base LP
            first["n"] = 1
            return REAL(c, **kw)
        r = REAL(c, **kw)
        if lbs[1] == u:          # exact floor (OUT lb == opt): pretend failure
            class F: success = False; message = "forced"
            return F()
        return r
    monkeypatch.setattr(fvamod, "linprog", fake)
    out = FVA(chain(u))
    slack = 1e-9 * max(1.0, abs(u))
    relaxed = [c for c in calls[1:] if c[1][1] != u]
    assert len(relaxed) == 4  # 2 reactions x 2 signs
    for _, lbs in relaxed:
        assert lbs[1] == pytest.approx(u - slack, rel=0, abs=1e-12 * max(1.0, u))
    # sign vectors: exactly +1 then -1 on the reaction index, per reaction
    vecs = [tuple(c[0]) for c in calls[1:] if c[1][1] == u]
    assert vecs == [(1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0)]
    assert out["optimum"] == u
