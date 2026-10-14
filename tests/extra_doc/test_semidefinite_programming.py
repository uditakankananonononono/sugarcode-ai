import copy
import random
from fractions import Fraction
from math import isqrt

import pytest

from sugarcode.extra_doc import semidefinite_programming as m
from sugarcode.extra_doc.semidefinite_programming import SdpError, semidefinite_programming as run

KEYS = "data keys must be exactly C, trace, constraint"
F = Fraction
SC = 10 ** 40


def d(C=(1, 1, 3), t=2, con=None):
    return {"C": list(C), "trace": t, "constraint": con}


def bad(data, msg):
    with pytest.raises(SdpError) as e:
        run(data)
    assert str(e.value) == msg


def approx(key, rad):
    """Fraction approximation (error below 1e-39) of key[0] + key[1]*sqrt(rad), no float."""
    a, b = F(key[0]), F(key[1])
    root = F(isqrt(rad * SC * SC), SC)
    return a + b * root


def objective(C, x, y, z):
    return C[0] * x + 2 * C[1] * y + C[2] * z


# ---- independent oracle -------------------------------------------------------------------------------
def lam_min_poly(C):
    """smaller root of l^2 - (c11 + c22) l + (c11 c22 - c12^2); returns (tr, det) for polynomial checks."""
    return C[0] + C[2], C[0] * C[2] - C[1] ** 2


def test_no_constraint_value_is_t_times_smallest_eigenvalue_root_of_characteristic_polynomial():
    rng = random.Random(245)
    nonint = 0
    for _ in range(300):
        C = [rng.randint(-20, 20), rng.randint(-20, 20), rng.randint(-20, 20)]
        t = rng.randint(1, 50)
        out = run(d(C, t))
        tr, dt = lam_min_poly(C)
        rad = out["radicand"]
        w = approx(out["dual_certificate"]["multiplier"], rad)
        # w is a root of its characteristic polynomial, and the smaller one
        assert abs(w * w - tr * w + dt) < F(1, 10 ** 30), C
        disc = F(tr * tr - 4 * dt)  # = (c11-c22)^2 + 4 c12^2
        other = tr - w
        assert w <= other
        assert (w - other) ** 2 - disc < F(1, 10 ** 30)
        assert approx(out["optimal_value"], rad) == t * w
        nonint += out["optimal_value"][1] != "0"
        assert out["trace_ok"] and out["constraint_ok"] and out["psd_ok"] and out["value_ok"]
        c = out["dual_certificate"]
        assert c["slack_psd"] and c["complementarity_zero"] and c["dual_value_equals_primal"]
        # rank one optimizer: x z = y^2 exactly
        x, y, z = (approx(out["optimizer"][k], rad) for k in "xyz")
        assert abs(x * z - y * y) < F(1, 10 ** 30)
        assert abs(x + z - t) < F(1, 10 ** 30) and x >= 0 and z >= 0
        # nothing feasible beats it: rational boundary points of the PSD disk, parametrized by the tangent half-angle
        for k in range(-6, 7):
            for j in range(0, 4):
                tt = F(k, 3) + F(j, 7)
                cv, sv = (1 - tt * tt) / (1 + tt * tt), 2 * tt / (1 + tt * tt)
                vv, yy = F(t, 2) * cv, F(t, 2) * sv
                assert objective(C, F(t, 2) + vv, yy, F(t, 2) - vv) >= approx(out["optimal_value"], rad) - F(1, 10 ** 30)
    assert nonint > 100


def test_perfect_square_discriminant_collapses_to_rational():
    # C = [[3,4],[4,-3]] has eigenvalues +-5: trace 6 gives -30 at a rational rank-one X
    out = run(d([3, 4, -3], 6))
    assert out["radicand"] == 1 and out["optimal_value"] == ["-30", "0"]
    x, y, z = (F(out["optimizer"][k][0]) for k in "xyz")
    assert all(out["optimizer"][k][1] == "0" for k in "xyz")
    assert x + z == 6 and x * z == y * y and objective([3, 4, -3], x, y, z) == -30


def test_hand_case_two_by_two_with_irrational_optimum():
    out = run(d([1, 1, 3], 2))
    assert out["radicand"] == 2 and out["optimal_value"] == ["4", "-2"]
    assert out["optimizer"] == {"x": ["1", "1/2"], "y": ["0", "-1/2"], "z": ["1", "-1/2"]}
    assert out["dual_certificate"]["multiplier"] == ["2", "-1"] and out["optimizer_unique"] is True


def test_identity_objective_has_non_unique_optimizer_and_value_is_trace():
    out = run(d([5, 0, 5], 4))
    assert out["optimal_value"] == ["20", "0"] and out["optimizer_unique"] is False
    assert out["optimizer"] == {"x": ["2", "0"], "y": ["0", "0"], "z": ["2", "0"]}
    out = run(d([0, 0, 0], 7))
    assert out["optimal_value"] == ["0", "0"] and out["optimizer_unique"] is False
    assert out["dual_certificate"]["dual_value_equals_primal"] is True


def sample_chord(C, t, A, b, out):
    """independent: points on the line inside the disk, found by solving |f + tau e|^2 = u^2 on rationals."""
    u = F(t, 2)
    r, s = F(A[0] - A[2]), F(2 * A[1])
    g = b - F(A[0] + A[2]) * u
    N2 = r * r + s * s
    f = (g * r / N2, g * s / N2)
    e = (-s, r)
    tau2 = (u * u - (f[0] ** 2 + f[1] ** 2)) / N2  # e has squared length N2
    return f, e, tau2


def test_constrained_optimum_is_the_better_chord_endpoint_and_beats_a_dense_chord_sample():
    rng = random.Random(7245)
    seen = {"irr": 0, "pt": 0, "nonuniq": 0, "inf": 0, "ok": 0}
    for _ in range(400):
        C = [rng.randint(-9, 9) for _ in range(3)]
        A = [rng.randint(-6, 6) for _ in range(3)]
        t = rng.randint(1, 12)
        b = rng.randint(-40, 40)
        try:
            out = run(d(C, t, {"A": A, "b": b}))
        except SdpError as e:
            assert str(e) == "constraint is infeasible"
            r, s = A[0] - A[2], 2 * A[1]
            g = F(b) - F(A[0] + A[2]) * F(t, 2)
            assert (r == s == 0 and g != 0) or (g * g > F(t, 2) ** 2 * (r * r + s * s))
            seen["inf"] += 1
            continue
        seen["ok"] += 1
        rad = out["radicand"]
        assert out["dual_certificate"] is None
        assert out["trace_ok"] and out["constraint_ok"] and out["psd_ok"] and out["value_ok"]
        val = approx(out["optimal_value"], rad)
        x, y, z = (approx(out["optimizer"][k], rad) for k in "xyz")
        assert abs(objective(C, x, y, z) - val) < F(1, 10 ** 30)
        assert abs(A[0] * x + 2 * A[1] * y + A[2] * z - b) < F(1, 10 ** 30) and abs(x + z - t) < F(1, 10 ** 30)
        r, s = A[0] - A[2], 2 * A[1]
        if r == 0 and s == 0:
            continue
        f, e, tau2 = sample_chord(C, t, A, b, out)
        u = F(t, 2)
        p, q = F(C[0] - C[2]), F(2 * C[1])
        if tau2 == 0:
            seen["pt"] += 1
            assert out["radicand"] == 1
        # endpoints via tau = +-sqrt(tau2) in high precision, independent of the module's squarefree reduction
        # sqrt(tau2) = isqrt(num*den*SC^2)/(den*SC)
        root = F(isqrt(tau2.numerator * tau2.denominator * SC * SC), tau2.denominator * SC)
        ends = []
        for sg in (1, -1):
            vv, yy = f[0] + sg * root * e[0], f[1] + sg * root * e[1]
            ends.append(F(C[0] + C[2], 2) * t + p * vv + q * yy)
        assert abs(val - min(ends)) < F(1, 10 ** 30)
        seen["irr"] += out["optimal_value"][1] != "0"
        if abs(ends[0] - ends[1]) < F(1, 10 ** 30):
            seen["nonuniq"] += 1
            assert out["optimizer_unique"] is False
        else:
            assert out["optimizer_unique"] is True
        for k in range(-9, 10):  # dense interior chord sample never beats the optimum
            tau = root * F(k, 9)
            vv, yy = f[0] + tau * e[0], f[1] + tau * e[1]
            assert F(C[0] + C[2], 2) * t + p * vv + q * yy >= val - F(1, 10 ** 30)
    assert seen["irr"] >= 50 and seen["inf"] >= 10 and seen["ok"] >= 100


def test_tangent_line_gives_the_single_feasible_point():
    # A = diag(1,-1): <A,X> = 2v; b = 4 gives v = 2 = u when t = 4: the line touches the disk at (2, 0), X = diag(4, 0)
    out = run(d([1, 0, 5], 4, {"A": [1, 0, -1], "b": 4}))
    assert out["radicand"] == 1 and out["optimizer"] == {"x": ["4", "0"], "y": ["0", "0"], "z": ["0", "0"]}
    assert out["optimal_value"] == ["4", "0"] and out["optimizer_unique"] is True


def test_constrained_hand_case_and_degenerate_constraints():
    out = run(d([1, 1, 3], 4, {"A": [1, 0, -1], "b": 1}))
    assert out["radicand"] == 15 and out["optimal_value"] == ["7", "-1"]
    assert out["optimizer"] == {"x": ["5/2", "0"], "y": ["0", "-1/2"], "z": ["3/2", "0"]}
    # constraint 0 = 0 is vacuous: same as no constraint; constraint with a = 0 and b != 0 is infeasible
    a = run(d([1, 1, 3], 2, {"A": [0, 0, 0], "b": 0}))
    b = run(d([1, 1, 3], 2))
    assert a == b
    bad(d([1, 1, 3], 2, {"A": [0, 0, 0], "b": 1}), "constraint is infeasible")
    # trace-like constraint a11 = a22 = 1: <A,X> = trace, so b = t is vacuous and b != t infeasible
    assert run(d([1, 1, 3], 2, {"A": [1, 0, 1], "b": 2})) == b
    bad(d([1, 1, 3], 2, {"A": [1, 0, 1], "b": 3}), "constraint is infeasible")
    bad(d([1, 0, 1], 2, {"A": [1, 0, -1], "b": 3}), "constraint is infeasible")  # 2v = 3, |v| <= 1


def test_flat_objective_along_chord_reports_non_unique():
    out = run(d([1, 0, 1], 4, {"A": [1, 0, -1], "b": 1}))
    assert out["optimal_value"] == ["4", "0"] and out["optimizer_unique"] is False


def test_constants_and_caps():
    assert (m.MAX_ENTRY, m.MAX_TRACE, m.MAX_B) == (20, 50, 1000)
    run(d([20, -20, 20], 50))
    run(d([-20, 20, -20], 1))
    bad(d([21, 0, 0]), "C entry out of range")
    bad(d([0, -21, 0]), "C entry out of range")
    bad(d([0, 0, 21]), "C entry out of range")
    bad(d(t=0), "trace out of range")
    bad(d(t=51), "trace out of range")
    bad(d(con={"A": [0, 0, 21], "b": 0}), "A entry out of range")
    bad(d(con={"A": [1, 0, 0], "b": 1001}), "b out of range")
    bad(d(con={"A": [1, 0, 0], "b": -1001}), "b out of range")
    run(d(con={"A": [1, 0, -1], "b": 0}))
    out = run(d([20, -20, 20], 50, {"A": [20, 20, -20], "b": 1000}))  # all caps at once
    assert out["trace_ok"] and out["constraint_ok"] and out["psd_ok"] and out["value_ok"]


def test_caps_before_scans_and_shape_errors():
    bad(d(t=10 ** 9), "trace out of range")
    bad({"C": [1, 2], "trace": 2, "constraint": None}, "C must be a list of 3 ints")
    bad({"C": [1, 2, 3, 4], "trace": 2, "constraint": None}, "C must be a list of 3 ints")
    bad({"C": (1, 2, 3), "trace": 2, "constraint": None}, "C must be a list of 3 ints")
    bad(d(con={"A": [1, 2], "b": 0}), "A must be a list of 3 ints")
    bad(d(con=[]), "constraint must be None or have keys exactly A, b")
    bad(d(con={"A": [1, 0, 0]}), "constraint must be None or have keys exactly A, b")
    bad(d(con={"A": [1, 0, 0], "b": 0, "x": 1}), "constraint must be None or have keys exactly A, b")
    bad([], KEYS)
    bad(None, KEYS)
    bad({}, KEYS)
    bad(d() | {"x": 1}, KEYS)


def test_nonbool_fixtures():
    for v in (True, False, 1.0, "1", None, [1]):
        bad(d([v, 0, 0]), "C entry must be an int")
        bad(d(t=v), "trace must be an int")
        bad(d(con={"A": [v, 0, 0], "b": 0}), "A entry must be an int")
        bad(d(con={"A": [1, 0, 0], "b": v}), "b must be an int")


def test_claims_purity_no_float():
    out = run(d())
    assert out["claims"] == {"models_real_problem": False, "larger_matrices": False,
                             "unreported_certificate": False, "real_world": False}
    out["claims"]["real_world"] = True
    out["not_claimed"].append("x")
    again = run(d())
    assert again["claims"]["real_world"] is False and again["not_claimed"] == list(m.NOT_CLAIMED)
    assert len(m.NOT_CLAIMED) == 4 and "Not claimed:" in m.__doc__
    x = d([3, 2, 5], 9, {"A": [1, 1, -1], "b": 2})
    y = copy.deepcopy(x)
    assert run(x) == run(x) and x == y

    def walk(v):
        assert not isinstance(v, float)
        if isinstance(v, dict):
            [walk(q) for q in v.values()]
        elif isinstance(v, list):
            [walk(q) for q in v]
    walk(out)


def test_surd_sign_matches_high_precision_for_every_sign_pattern():
    rng = random.Random(99)
    seen = set()
    for _ in range(3000):
        mm = rng.choice([1, 2, 3, 5, 6, 7, 10, 11, 15, 30])
        a = F(rng.randint(-9, 9), rng.randint(1, 4))
        b = F(rng.randint(-9, 9), rng.randint(1, 4))
        got = m._S(a, b, mm).sign()
        val = a + b * F(isqrt(mm * SC * SC), SC)
        if mm == 1:
            want = (a + b > 0) - (a + b < 0)
        elif abs(val) > F(1, 10 ** 30):
            want = (val > 0) - (val < 0)
        else:
            want = 0  # only a = b = 0 can give an exact zero for squarefree m > 1
            assert a == 0 and b == 0
        assert got == want, (a, b, mm)
        seen.add((mm == 1, (a > 0) - (a < 0), (b > 0) - (b < 0), want))
    # all sign combinations of (a, b) for m > 1 occurred, including opposite signs with either result
    for sa in (-1, 0, 1):
        for sb in (-1, 0, 1):
            for w in (-1, 0, 1):
                if (sa, sb, w) in {(1, -1, 1), (1, -1, -1), (-1, 1, 1), (-1, 1, -1)}:
                    assert (False, sa, sb, w) in seen
    assert m._S(7, -5, 2).sign() == -1 and m._S(-7, 5, 2).sign() == 1  # 7 - 5*sqrt(2) = -0.0711
    assert m._S(3, -2, 3).sign() == -1 and m._S(2, -1, 3).sign() == 1 and m._S(-2, 1, 3).sign() == -1
    assert m._S(5, 3, 1).sign() == 1 and m._S(-5, 3, 1).sign() == -1 and m._S(-3, 3, 1).sign() == 0


def test_squarefree_reduction():
    for q, k, mm in ((F(8), F(2), 2), (F(1, 2), F(1, 2), 2), (F(12), F(2), 3), (F(9), F(3), 1), (F(5), F(1), 5), (F(50, 9), F(5, 3), 2), (F(1), F(1), 1)):
        assert m._squarefree(q) == (k, mm), q
        assert k * k * mm == q


def test_radicand_and_infeasible_boundary_pins():
    assert run(d([5, 0, 5], 4))["radicand"] == 1 and run(d([0, 0, 0], 7))["radicand"] == 1
    # t = 2 (u = 1), A = [[1,1],[1,-1]]: 2v + 2y = 3 has squared distance gap R = u^2 N^2 - g^2 = 8 - 9 = -1
    bad(d([1, 0, 1], 2, {"A": [1, 1, -1], "b": 3}), "constraint is infeasible")
    assert run(d([1, 0, 1], 2, {"A": [1, 1, -1], "b": 2}))["trace_ok"]  # R = 8 - 4 > 0


def test_flat_chord_optimizer_is_the_tau_minus_endpoint():
    out = run(d([1, 0, 1], 4, {"A": [1, 0, -1], "b": 1}))
    # u = 2, r = 2, s = 0, g = 1: v = 1/2, y = +-sqrt(15)/2; tau = -1 selects the endpoint with y = -sqrt(15)/2
    assert out["optimizer"] == {"x": ["5/2", "0"], "y": ["0", "-1/2"], "z": ["3/2", "0"]}
    assert out["radicand"] == 15 and out["optimizer_unique"] is False


def test_identity_objective_certificate_and_tangent_cases_with_nonzero_coordinates():
    out = run(d([5, 0, 5], 4))
    assert out["dual_certificate"] == {"multiplier": ["5", "0"], "slack_psd": True,
                                       "complementarity_zero": True, "dual_value_equals_primal": True}
    # tangent with y != 0: A = [[0,1],[1,0]] gives 2y = b; t = 4, b = 4 -> y = 2 = u, v = 0, X = [[2,2],[2,2]], <C,X> = 12
    out = run(d([1, 1, 3], 4, {"A": [0, 1, 0], "b": 4}))
    assert out["radicand"] == 1 and out["optimal_value"] == ["12", "0"]
    assert out["optimizer"] == {"x": ["2", "0"], "y": ["2", "0"], "z": ["2", "0"]}
    out = run(d([1, 1, 3], 4, {"A": [0, 1, 0], "b": -4}))
    assert out["optimal_value"] == ["4", "0"] and out["optimizer"]["y"] == ["-2", "0"]  # x = z = 2, y = -2: 2 - 4 + 6
    # tangent with both foot coordinates nonzero: t = 2, A = [[2,2],[2,-1]], b = 6 -> foot (3/5, 4/5), X = [[8/5,4/5],[4/5,2/5]]
    out = run(d([1, 1, 3], 2, {"A": [2, 2, -1], "b": 6}))
    assert out["radicand"] == 1 and out["optimal_value"] == ["22/5", "0"]
    assert out["optimizer"] == {"x": ["8/5", "0"], "y": ["4/5", "0"], "z": ["2/5", "0"]}
    out = run(d([-3, 2, 4], 2, {"A": [2, 2, -1], "b": 6}))  # same X: -3*8/5 + 2*2*4/5 + 4*2/5 = 0
    assert out["optimal_value"] == ["0", "0"]


def squarefree_part(n):
    """independent of the module: strip squares by dividing out s*s for s descending from isqrt(n)."""
    n = int(n)
    for s in range(isqrt(n), 1, -1):
        while n % (s * s) == 0:
            n //= s * s
    return n


def test_radicand_is_the_squarefree_part_in_every_case():
    rng = random.Random(2451)
    seen = {"m1": 0, "mbig": 0, "con": 0}
    for _ in range(600):
        C = [rng.randint(-20, 20) for _ in range(3)]
        t = rng.randint(1, 50)
        con = None
        if rng.random() < 0.5:
            con = {"A": [rng.randint(-6, 6) for _ in range(3)], "b": rng.randint(-60, 60)}
        try:
            out = run(d(C, t, con))
        except SdpError:
            continue
        u = F(t, 2)
        p, q = F(C[0] - C[2]), F(2 * C[1])
        if con is None or (con["A"][0] == con["A"][2] and con["A"][1] == 0):
            rad = p * p + q * q
        else:
            A = con["A"]
            r, s = F(A[0] - A[2]), F(2 * A[1])
            g = con["b"] - F(A[0] + A[2]) * u
            rad = u * u * (r * r + s * s) - g * g
        want = 1 if rad == 0 else squarefree_part(rad.numerator * rad.denominator)
        assert out["radicand"] == want, (C, t, con)
        seen["m1"] += want == 1
        seen["mbig"] += want > 1
        seen["con"] += con is not None
        # irrational parts only appear with a radicand above 1, and the key pair is [rational, sqrt coefficient]
        if want == 1:
            for k in ("x", "y", "z"):
                assert out["optimizer"][k][1] == "0"
            assert out["optimal_value"][1] == "0"
    assert min(seen.values()) >= 15
    # the flat-C case the audit named: C = [1,0,1], trace 2, no constraint: rational, radicand exactly 1
    out = run(d([1, 0, 1], 2))
    assert out["radicand"] == 1 and out["optimal_value"] == ["2", "0"]
    assert out["optimizer"] == {"x": ["1", "0"], "y": ["0", "0"], "z": ["1", "0"]}
    o = run(d([2, 1, 5], 2))  # p = -3, q = 2, p^2 + q^2 = 13 (already squarefree)
    assert o["radicand"] == 13 and o["optimal_value"] == ["7", "-1"]
    o = run(d([4, 2, 0], 1))  # p = 4, q = 4, p^2 + q^2 = 32 = 16 * 2: radicand 2, not 32 or 1
    assert o["radicand"] == 2 and o["optimal_value"] == ["2", "-2"]
    assert run(d([3, 0, -3], 1))["radicand"] == 1  # p^2 + q^2 = 36, a perfect square


def test_surd_sign_exhaustive_over_small_fractions():
    fr = sorted({F(n, dd) for n in range(-12, 13) for dd in (1, 2, 3)})
    for mm in (1, 2, 3, 5, 6, 7, 10, 11, 13, 15):
        root = F(isqrt(mm * SC * SC), SC)
        for a in fr:
            for b in fr:
                got = m._S(a, b, mm).sign()
                if mm == 1:
                    want = ((a + b) > 0) - ((a + b) < 0)
                else:
                    val = a + b * root
                    want = 0 if (a == 0 and b == 0) else (val > 0) - (val < 0)
                    assert (a == 0 and b == 0) or abs(val) > F(1, 10 ** 30)
                assert got == want, (a, b, mm)
