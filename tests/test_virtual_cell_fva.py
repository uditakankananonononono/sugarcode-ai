"""virtual_cell unit 43: flux variability analysis (FVA). Oracle: exhaustive vertex enumeration
of {S v = 0, lb <= v <= ub, objective >= f*opt} in exact Fractions (independent of linprog)."""
from fractions import Fraction as F
import itertools
import numpy as np
import pytest
from sugarcode.modules.virtual_cell import central_carbon_model, demo_model, fba, MetabolicModel
from sugarcode.modules.virtual_cell.fva import flux_variability


def solve(A, b):
    n = len(A); M = [row[:] + [bb] for row, bb in zip(A, b)]
    for c in range(n):
        p = next((r for r in range(c, n) if M[r][c] != 0), None)
        if p is None:
            return None
        M[c], M[p] = M[p], M[c]; pv = M[c][c]; M[c] = [x / pv for x in M[c]]
        for r in range(n):
            if r != c and M[r][c] != 0:
                f = M[r][c]; M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return [M[i][n] for i in range(n)]


def vertices(model, obj_lb=None):
    S = [[F(float(x)).limit_denominator(1000) for x in row] for row in model.S]
    lb = [F(float(x)) for x in model.lb]; ub = [F(float(x)) for x in model.ub]
    n = len(lb); oi = model.reactions.index(model.objective)
    cons = []  # (var, value)
    for i in range(n):
        cons.append((i, lb[i])); cons.append((i, ub[i]))
    if obj_lb is not None:
        cons.append((oi, obj_lb))
    m = len(S); verts = set()
    for sub in itertools.combinations(range(len(cons)), n - np.linalg.matrix_rank(model.S)):
        A = [r[:] for r in S]; b = [F(0)] * m
        for k in sub:
            row = [F(0)] * n; row[cons[k][0]] = F(1); A.append(row); b.append(cons[k][1])
        # square system needs n rows: pick independent subset of equations via rank trick
        # use all rows least-squares-free: choose first n independent rows
        rows = []; rhs = []
        for r, bb in zip(A, b):
            test = rows + [r]
            if np.linalg.matrix_rank(np.array([[float(x) for x in t] for t in test])) == len(test):
                rows.append(r); rhs.append(bb)
        if len(rows) != n:
            continue
        v = solve(rows, rhs)
        if v is None:
            continue
        if all(lb[i] <= v[i] <= ub[i] for i in range(n)) and all(sum(S[k][i] * v[i] for i in range(n)) == 0 for k in range(m)) \
                and (obj_lb is None or v[oi] >= obj_lb):
            verts.add(tuple(v))
    return verts


@pytest.mark.parametrize("factory,frac", [(demo_model, F(1, 2)), (demo_model, F(1)), (central_carbon_model, F(9, 10))])
def test_ranges_match_vertex_enumeration(factory, frac):
    m = factory()
    allv = vertices(m)
    oi = m.reactions.index(m.objective)
    opt = max(v[oi] for v in allv)
    assert float(opt) == pytest.approx(fba(m)["objective"], abs=1e-5)
    verts = vertices(m, frac * opt)
    r = flux_variability(m, fraction_of_optimum=float(frac))
    for i, name in enumerate(m.reactions):
        lo = min(v[i] for v in verts); hi = max(v[i] for v in verts)
        assert r["ranges"][name]["min"] == pytest.approx(float(lo), abs=1e-5), name
        assert r["ranges"][name]["max"] == pytest.approx(float(hi), abs=1e-5), name


def test_blocked_and_fixed_flags():
    r = flux_variability(demo_model(), fraction_of_optimum=1.0)
    assert r["ranges"]["GLYCOLYSIS"]["fixed"] is True and r["ranges"]["GLYCOLYSIS"]["max"] == pytest.approx(10.0, abs=1e-6)
    r2 = flux_variability(demo_model(), fraction_of_optimum=0.5)
    assert r2["ranges"]["GLYCOLYSIS"]["fixed"] is False
    assert r2["ranges"]["GLYCOLYSIS"]["min"] == pytest.approx(5.0, abs=1e-6)


def test_reports_infeasible_instead_of_zeros():
    r = flux_variability(demo_model(), bounds_override={"GLC_UP": (0, 0)}, fraction_of_optimum=1.0)
    assert r["status"] == "optimal" and r["ranges"]["BIOMASS"]["max"] == pytest.approx(0.0, abs=1e-9)
    bad = flux_variability(demo_model(), bounds_override={"BIOMASS": (100, 200)})
    assert bad["status"] == "infeasible" and bad["ranges"] == {}


@pytest.mark.parametrize("kw", [
    dict(fraction_of_optimum=True), dict(fraction_of_optimum=float("nan")), dict(fraction_of_optimum=1.5),
    dict(fraction_of_optimum=-0.1), dict(fraction_of_optimum=10**400),
    dict(objective="NOPE"), dict(bounds_override={"NOPE": (0, 1)}), dict(bounds_override={"GLC_UP": (5, 1)}),
    dict(bounds_override={"GLC_UP": (0, float("nan"))}), dict(bounds_override={"GLC_UP": (True, 1)}),
    dict(bounds_override={"GLC_UP": (0,)}), dict(bounds_override=[1])])
def test_rejects_bad_input(kw):
    with pytest.raises((ValueError, TypeError)):
        flux_variability(demo_model(), **kw)


def test_rejects_bad_model():
    with pytest.raises(TypeError):
        flux_variability("model")
    m = demo_model(); m.S = m.S.copy(); m.S[0, 0] = float("nan")
    with pytest.raises(ValueError):
        flux_variability(m)
    m2 = demo_model(); m2.lb = m2.lb.copy(); m2.lb[0] = 50
    with pytest.raises(ValueError):
        flux_variability(m2)


def test_status_partial():
    assert "PARTIAL" in flux_variability(demo_model())["status_note"]


@pytest.mark.parametrize("tol", [True, -1.0, float("nan")])
def test_rejects_bad_tol(tol):
    with pytest.raises((ValueError, TypeError)):
        flux_variability(demo_model(), tol=tol)
