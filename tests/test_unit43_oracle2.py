"""Second, independent oracle for virtual_cell.fva.flux_variability (written without reading the builder tests).
Exact oracle: totally unimodular networks (every column has at most one +1 and one -1) with integer bounds have
integral vertices, so exhaustive enumeration of integer flux vectors gives the exact FVA ranges (no LP, no fractions of
vertices). Plus hand-derived literals, validation pins and cap pins (linprog stubbed for the 2000-reaction edge)."""
import itertools
import math
import random
import numpy as np
import pytest
from sugarcode.modules.virtual_cell import fva as fvamod
from sugarcode.modules.virtual_cell.core import MetabolicModel
from sugarcode.modules.virtual_cell.fva import flux_variability as FVA


def model(S, lb, ub, rx=None, obj=None):
    S = np.array(S, float)
    rx = rx or ["R%d" % i for i in range(S.shape[1])]
    return MetabolicModel(["M%d" % i for i in range(S.shape[0])], rx, S, np.array(lb, float), np.array(ub, float), obj or rx[-1])


def enum_oracle(S, lb, ub, oi, f):
    S = np.array(S, int)
    feas = [v for v in itertools.product(*[range(l, u + 1) for l, u in zip(lb, ub)])
            if not (S @ np.array(v)).any()]
    if not feas:
        return None
    opt = max(v[oi] for v in feas)
    bound = opt - (1 - f) * abs(opt)
    keep = [v for v in feas if v[oi] >= bound - 1e-9]
    return opt, bound, [(min(v[i] for v in keep), max(v[i] for v in keep)) for i in range(len(lb))]


def random_tu(rng, n_met, n_rx):
    S = np.zeros((n_met, n_rx), int)
    for j in range(n_rx):
        kind = rng.random()
        a = rng.randrange(n_met)
        if kind < .3:
            S[a, j] = rng.choice([1, -1])
        else:
            b = rng.randrange(n_met)
            if b != a:
                S[a, j], S[b, j] = 1, -1
    return S


# ---- hand-derived literals ----
def parallel():
    # R0: -> A [0,10]; R1,R2: A -> B [0,6] each; R3 (objective): B -> [0,100]
    S = [[1, -1, -1, 0], [0, 1, 1, -1]]
    return model(S, [0, 0, 0, 0], [10, 6, 6, 100], ["UP", "P1", "P2", "BIO"])


def test_parallel_paths_literal():
    r = FVA(parallel())
    assert r["status"] == "optimal" and r["objective"] == "BIO" and r["optimum"] == pytest.approx(10)
    assert r["objective_bound"] == pytest.approx(10) and r["fraction_of_optimum"] == 1.0
    want = {"UP": (10, 10), "P1": (4, 6), "P2": (4, 6), "BIO": (10, 10)}
    for k, (lo, hi) in want.items():
        assert r["ranges"][k]["min"] == pytest.approx(lo, abs=1e-6) and r["ranges"][k]["max"] == pytest.approx(hi, abs=1e-6)
    assert r["ranges"]["UP"]["fixed"] and r["ranges"]["BIO"]["fixed"] and not r["ranges"]["P1"]["fixed"]
    assert not any(v["blocked"] for v in r["ranges"].values())
    r5 = FVA(parallel(), fraction_of_optimum=0.5)
    assert r5["objective_bound"] == pytest.approx(5)
    assert (r5["ranges"]["UP"]["min"], r5["ranges"]["UP"]["max"]) == (pytest.approx(5), pytest.approx(10))
    assert (r5["ranges"]["P1"]["min"], r5["ranges"]["P1"]["max"]) == (pytest.approx(0, abs=1e-6), pytest.approx(6))
    r0 = FVA(parallel(), fraction_of_optimum=0.0)
    assert r0["objective_bound"] == pytest.approx(0) and r0["ranges"]["BIO"]["min"] == pytest.approx(0, abs=1e-6)
    assert r0["ranges"]["BIO"]["max"] == pytest.approx(10)


def test_blocked_dead_end_and_knockout_override():
    # R0: -> A [0,5]; R1: A -> B [0,5]; R2 (obj): A -> [0,5]; R3: B -> C [0,5] (C dead end: nothing consumes C) -> R3 blocked
    S = [[1, -1, -1, 0], [0, 1, 0, -1], [0, 0, 0, 1]]
    m = model(S, [0] * 4, [5] * 4, ["UP", "AB", "OBJ", "BC"], "OBJ")
    r = FVA(m)
    assert r["optimum"] == pytest.approx(5)
    assert r["ranges"]["AB"]["blocked"] and r["ranges"]["BC"]["blocked"] and r["ranges"]["BC"]["fixed"]
    assert not r["ranges"]["OBJ"]["blocked"]
    # knockout of UP: optimum 0, everything fixed and blocked
    k = FVA(m, bounds_override={"UP": (0, 0)})
    assert k["optimum"] == pytest.approx(0, abs=1e-9)
    assert all(v["fixed"] and v["blocked"] for v in k["ranges"].values())
    # override with a list pair and with ints/floats, model unchanged
    FVA(m, bounds_override={"UP": [0, 3.0]})
    assert list(m.ub) == [5, 5, 5, 5] and list(m.lb) == [0] * 4


def test_negative_optimum_convention():
    # objective flux forced into [-5,-2]; balance via UP [-5,0]: S: A: UP - OBJ... use single metabolite A: UP (+1) , OBJ (-1)
    m = model([[1, -1]], [-5, -5], [5, -2], ["UP", "OBJ"], "OBJ")
    r = FVA(m)
    assert r["optimum"] == pytest.approx(-2) and r["objective_bound"] == pytest.approx(-2)
    r5 = FVA(m, fraction_of_optimum=0.5)                 # bound = opt - 0.5*|opt| = -3
    assert r5["objective_bound"] == pytest.approx(-3)
    assert (r5["ranges"]["OBJ"]["min"], r5["ranges"]["OBJ"]["max"]) == (pytest.approx(-3), pytest.approx(-2))
    assert (r5["ranges"]["UP"]["min"], r5["ranges"]["UP"]["max"]) == (pytest.approx(-3), pytest.approx(-2))
    r0 = FVA(m, fraction_of_optimum=0.0)                 # bound = -4
    assert r0["objective_bound"] == pytest.approx(-4) and r0["ranges"]["OBJ"]["min"] == pytest.approx(-4)


def test_infeasible_status():
    m = model([[1, -1]], [2, 0], [3, 1], ["UP", "OBJ"], "OBJ")       # UP >= 2 but OBJ <= 1 and UP = OBJ
    r = FVA(m)
    assert r["status"] == "infeasible" and r["optimum"] is None and r["objective_bound"] is None
    assert r["ranges"] == {} and r["objective"] == "OBJ" and "PARTIAL" in r["status_note"]
    assert "fraction_of_optimum" not in r


def test_objective_argument_and_default():
    m = parallel()
    r = FVA(m, objective="UP")
    assert r["objective"] == "UP" and r["optimum"] == pytest.approx(10)
    r2 = FVA(m, objective="P1")
    assert r2["objective"] == "P1" and r2["optimum"] == pytest.approx(6)
    assert FVA(m, objective=None)["objective"] == "BIO"
    assert FVA(m, objective="")["objective"] == "BIO"                  # falsy objective falls back to the model's
    with pytest.raises(ValueError, match="unknown objective"):
        FVA(m, objective="nope")


def test_tol_semantics():
    m = parallel()
    big = FVA(m, tol=100)
    assert all(v["fixed"] and v["blocked"] for v in big["ranges"].values())
    one = FVA(m, tol=2.0001)                                           # P1 spans [4,6]: width 2 -> fixed at tol 2.0001
    assert one["ranges"]["P1"]["fixed"] is True
    assert FVA(m, tol=1.999)["ranges"]["P1"]["fixed"] is False
    assert FVA(m, tol=np.float64(0.5))["status"] == "optimal" and FVA(m, tol=np.int64(1))["status"] == "optimal"
    # blocked needs both ends within tol of 0: P1 in [4,6] with tol 4.5 is not blocked, with tol 6 it is
    assert FVA(m, tol=4.5)["ranges"]["P1"]["blocked"] is False and FVA(m, tol=6)["ranges"]["P1"]["blocked"] is True


def test_tol_zero_reports_fixed_after_slack_leak_fix():
    """v4: was a characterization of the defect (objective relaxation leaked into min/max). Now pins the fix:
    a truly fixed reaction at f=1 reports min == max == opt exactly, so tol=0 gives fixed=True."""
    r = FVA(parallel(), tol=0)["ranges"]["UP"]
    assert r["fixed"] is True and r["min"] == 10 and r["max"] == 10
    big = model([[1, -1, -1, 0], [0, 1, 1, -1]], [0] * 4, [1e9, 6e8, 6e8, 1e12], ["UP", "P1", "P2", "BIO"])
    rb = FVA(big)["ranges"]["UP"]
    assert rb["min"] == pytest.approx(1e9, abs=1e-3) and rb["max"] == pytest.approx(1e9, abs=1e-3)
    assert rb["fixed"] is True                                           # at the default tol=1e-6


# ---- exhaustive vs integer enumeration ----
def test_random_tu_networks_match_integer_enumeration():
    rng = random.Random(43)
    done = 0
    while done < 120:
        nm, nr = rng.randint(1, 3), rng.randint(2, 5)
        S = random_tu(rng, nm, nr)
        lb = [rng.randint(-2, 1) for _ in range(nr)]
        ub = [l + rng.randint(0, 4) for l in lb]
        oi = rng.randrange(nr)
        f = rng.choice([1.0, 1.0, 0.0, 0.5])
        m = model(S, lb, ub, obj="R%d" % oi)
        want = enum_oracle(S, lb, ub, oi, f)
        if want is not None and f == 0.5 and (want[1] != int(want[1])):
            continue
        done += 1
        r = FVA(m, fraction_of_optimum=f)
        if want is None:
            assert r["status"] == "infeasible", (S.tolist(), lb, ub, oi)
            continue
        opt, bound, rngs = want
        assert r["status"] == "optimal" and r["optimum"] == pytest.approx(opt, abs=1e-6)
        assert r["objective_bound"] == pytest.approx(bound, abs=1e-6)
        for i, (lo, hi) in enumerate(rngs):
            x = r["ranges"]["R%d" % i]
            assert x["min"] == pytest.approx(lo, abs=1e-5) and x["max"] == pytest.approx(hi, abs=1e-5), (S.tolist(), lb, ub, oi, f, i)
            assert x["fixed"] == (hi - lo <= 1e-6) and x["blocked"] == (lo == 0 and hi == 0)


def test_input_model_not_mutated():
    m = parallel()
    S0, lb0, ub0 = m.S.copy(), m.lb.copy(), m.ub.copy()
    FVA(m, bounds_override={"UP": (1, 2)})
    assert (m.S == S0).all() and (m.lb == lb0).all() and (m.ub == ub0).all()


# ---- validation / caps ----
def bad(exc, match, **kw):
    with pytest.raises(exc, match=match):
        FVA(kw.pop("m", None) or parallel(), **kw)


def test_argument_validation():
    for v in (True, "0.5", None, [1], 1j):
        bad(TypeError, "fraction_of_optimum must be a real number", fraction_of_optimum=v)
    for v in (-0.1, 1.0000001, 2):
        bad(ValueError, "fraction_of_optimum must be in", fraction_of_optimum=v)
    for v in (float("nan"), float("inf"), -float("inf"), 1e13):
        bad(ValueError, "fraction_of_optimum must be finite|out of range|must be in", fraction_of_optimum=v)
    bad(ValueError, "out of range", fraction_of_optimum=10**13)
    for v in (True, "1", None):
        bad(TypeError, "tol must be a real number", tol=v)
    bad(ValueError, "tol must be >= 0", tol=-1e-9)
    bad(ValueError, "tol must be finite", tol=float("nan"))
    bad(ValueError, "tol must be finite", tol=2e12)
    bad(ValueError, "out of range", tol=10**12 + 1)
    assert FVA(parallel(), tol=10**12)["status"] == "optimal"
    assert FVA(parallel(), fraction_of_optimum=1)["fraction_of_optimum"] == 1.0
    assert FVA(parallel(), fraction_of_optimum=0)["fraction_of_optimum"] == 0.0
    assert FVA(parallel(), fraction_of_optimum=np.float32(0.5))["objective_bound"] == pytest.approx(5)
    assert FVA(parallel(), fraction_of_optimum=np.int64(1))["status"] == "optimal"


def test_bounds_override_validation():
    bad(TypeError, "must be a dict", bounds_override=[("UP", (0, 1))])
    bad(ValueError, "unknown reaction", bounds_override={"zz": (0, 1)})
    bad(ValueError, r"\(lo, hi\)", bounds_override={"UP": (0,)})
    bad(ValueError, r"\(lo, hi\)", bounds_override={"UP": 5})
    bad(ValueError, r"\(lo, hi\)", bounds_override={"UP": (0, 1, 2)})
    bad(ValueError, r"\(lo, hi\)", bounds_override={"UP": "ab"})
    bad(TypeError, "lower bound must be a real number", bounds_override={"UP": (True, 1)})
    bad(TypeError, "upper bound must be a real number", bounds_override={"UP": (0, "1")})
    bad(ValueError, "lower bound must be finite", bounds_override={"UP": (float("nan"), 1)})
    bad(ValueError, "upper bound must be finite", bounds_override={"UP": (0, float("inf"))})
    bad(ValueError, "lower bound exceeds|a lower bound exceeds", bounds_override={"UP": (3, 2)})
    bad(ValueError, "out of range", bounds_override={"UP": (0, 10**13)})
    assert FVA(parallel(), bounds_override={})["status"] == "optimal"
    assert FVA(parallel(), bounds_override={"UP": (0, 1e12)})["status"] == "optimal"


def test_model_validation():
    class Bare:  # missing attributes
        S = lb = ub = reactions = metabolites = []
    with pytest.raises(TypeError, match="must be a MetabolicModel"):
        FVA(Bare())
    with pytest.raises(TypeError, match="must be a MetabolicModel"):
        FVA(None)
    m = parallel(); m.reactions = []
    with pytest.raises(ValueError, match="needs 1..2000 reactions"):
        FVA(m)
    m = parallel(); m.S = np.full((2, 4), np.nan)
    with pytest.raises(ValueError, match="S must be finite"):
        FVA(m)
    m = parallel(); m.S = np.zeros((3, 4))
    with pytest.raises(ValueError, match="S must be finite"):
        FVA(m)
    m = parallel(); m.lb = np.array([0, 0, 0])
    with pytest.raises(ValueError, match="lb/ub must be finite"):
        FVA(m)
    m = parallel(); m.ub = np.array([1, 1, 1, np.inf])
    with pytest.raises(ValueError, match="lb/ub must be finite"):
        FVA(m)
    m = parallel(); m.lb = np.array([0, 0, 0, np.nan])
    with pytest.raises(ValueError, match="lb/ub must be finite"):
        FVA(m)
    m = parallel(); m.lb = np.array([5, 0, 0, 0]); m.ub = np.array([4, 6, 6, 9])
    with pytest.raises(ValueError, match="lower bound exceeds"):
        FVA(m)
    m = parallel()
    with pytest.raises(ValueError, match="2000"):
        FVA(model(np.zeros((1, 2001)), [0] * 2001, [1] * 2001))


def test_2000_reaction_edge_accepted_with_stubbed_lp(monkeypatch):
    calls = []

    class R:
        success = True
        fun = 0.0
        message = ""
        def __init__(self, n): self.x = np.zeros(n)

    def fake(c, A_eq=None, b_eq=None, bounds=None, method=None):
        calls.append(1)
        return R(len(c))
    monkeypatch.setattr(fvamod, "linprog", fake)
    r = FVA(model(np.zeros((1, 2000)), [0] * 2000, [1] * 2000))
    assert r["status"] == "optimal" and len(r["ranges"]) == 2000 and len(calls) == 1 + 2 * 2000
    r1 = FVA(model(np.zeros((1, 1)), [0], [1]))
    assert len(r1["ranges"]) == 1


def test_lp_failure_mid_scan_is_a_named_error(monkeypatch):
    real = fvamod.linprog
    state = {"n": 0}

    class Bad:
        success = False
        message = "boom"
        x = None
        fun = None

    def flaky(*a, **k):
        state["n"] += 1
        return real(*a, **k) if state["n"] <= 3 else Bad()
    monkeypatch.setattr(fvamod, "linprog", flaky)
    with pytest.raises(ValueError, match="FVA LP failed for .*boom"):
        FVA(parallel())


def test_note_and_keys():
    r = FVA(parallel())
    assert list(r) == ["status", "objective", "optimum", "fraction_of_optimum", "objective_bound", "ranges", "status_note"]
    assert list(r["ranges"]) == ["UP", "P1", "P2", "BIO"]
    assert set(r["ranges"]["UP"]) == {"min", "max", "fixed", "blocked"}
    assert r["status_note"].startswith("PARTIAL:") and "no wet-lab claim" in r["status_note"]
    assert type(r["ranges"]["UP"]["fixed"]) is bool and type(r["optimum"]) is float
