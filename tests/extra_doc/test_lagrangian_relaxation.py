import copy
import random
from fractions import Fraction

import pytest

from sugarcode.extra_doc import lagrangian_relaxation as m
from sugarcode.extra_doc.lagrangian_relaxation import LagrangeError, lagrangian_relaxation as run

KEYS = "data keys must be exactly costs, weights, demand"
F = Fraction


def d(costs=(10, 7, 4, 3), weights=(5, 4, 3, 2), demand=8):
    return {"costs": list(costs), "weights": list(weights), "demand": demand}


def bad(data, msg):
    with pytest.raises(LagrangeError) as e:
        run(data)
    assert str(e.value) == msg


# ---- independent oracle. The dual optimum equals the LP relaxation optimum (the subproblem has the
# ---- integrality property), computed here by a fractional greedy cover that shares no code with the module.
def lp_value(c, a, b):
    tot = F(0)
    need = b
    for ci, ai in zip(c, a):
        if ci < 0:
            tot += ci
            need -= ai
    rest = sorted(((F(ci, ai), ci, ai) for ci, ai in zip(c, a) if ci >= 0))
    for ratio, ci, ai in rest:
        if need <= 0:
            break
        take = min(F(1), F(need, ai))
        tot += take * ci
        need -= take * ai
    return tot


def brute(c, a, b):
    n = len(c)
    best = None
    for mask in range(2 ** n):
        x = [(mask >> (n - 1 - i)) & 1 for i in range(n)]  # lexicographic order of x
        if sum(ai * xi for ai, xi in zip(a, x)) >= b:
            v = sum(ci * xi for ci, xi in zip(c, x))
            if best is None or v < best[0]:
                best = (v, x)
    return best


def dual_by_enumeration(lam, c, a, b):
    # min over all x of the Lagrangian, no use of the separable shortcut
    n = len(c)
    best = None
    for mask in range(2 ** n):
        x = [(mask >> i) & 1 for i in range(n)]
        v = sum(ci * xi for ci, xi in zip(c, x)) + lam * (b - sum(ai * xi for ai, xi in zip(a, x)))
        best = v if best is None or v < best else best
    return best


def test_hand_case_exact_values():
    out = run(d())
    assert out["multiplier"] == "7/4" and out["dual_value"] == "49/4"
    assert out["relaxed_assignment"] == [0, 0, 1, 1] and out["relaxed_weight"] == 5 and out["relaxed_feasible"] is False
    assert out["primal_candidate"] == [0, 1, 1, 1] and out["primal_candidate_value"] == 14
    assert out["optimum_value"] == 14 and out["optimum_assignment"] == [0, 1, 1, 1]
    assert out["integrality_gap"] == "7/4" and out["candidate_gap"] == 0 and out["items"] == 4
    assert lp_value([10, 7, 4, 3], [5, 4, 3, 2], 8) == F(49, 4)


def test_matches_independent_oracle_on_random_instances():
    rng = random.Random(244)
    seen = {"gap": 0, "tight": 0, "feas": 0, "infeas": 0, "neg": 0, "cand_gap": 0}
    for _ in range(300):
        n = rng.randint(1, 8)
        c = [rng.randint(-20, 30) for _ in range(n)]
        a = [rng.randint(1, 12) for _ in range(n)]
        b = rng.randint(0, sum(a))
        out = run(d(c, a, b))
        dual = F(out["dual_value"])
        assert dual == lp_value(c, a, b), (c, a, b)
        lam = F(out["multiplier"])
        assert lam >= 0 and dual_by_enumeration(lam, c, a, b) == dual
        # no other multiplier on a fine rational grid beats it (concavity: grid plus breakpoints)
        for k in range(0, 41):
            g = F(k, 4)
            assert dual_by_enumeration(g, c, a, b) <= dual
        ov, ox = brute(c, a, b)
        assert out["optimum_value"] == ov and out["optimum_assignment"] == ox
        assert dual <= ov and F(out["integrality_gap"]) == ov - dual >= 0
        cx = out["primal_candidate"]
        assert sum(ai * xi for ai, xi in zip(a, cx)) >= b
        assert out["primal_candidate_value"] == sum(ci * xi for ci, xi in zip(c, cx)) >= ov
        assert out["candidate_gap"] == out["primal_candidate_value"] - ov
        rx = out["relaxed_assignment"]
        assert out["relaxed_feasible"] == (sum(ai * xi for ai, xi in zip(a, rx)) >= b)
        assert all(xi == (1 if F(ci) - lam * ai < 0 else 0) for ci, ai, xi in zip(c, a, rx))
        seen["gap"] += F(out["integrality_gap"]) > 0
        seen["tight"] += F(out["integrality_gap"]) == 0
        seen["feas"] += out["relaxed_feasible"]
        seen["infeas"] += not out["relaxed_feasible"]
        seen["neg"] += any(ci < 0 for ci in c)
        seen["cand_gap"] += out["candidate_gap"] > 0
    assert min(seen["gap"], seen["tight"], seen["feas"], seen["infeas"], seen["neg"]) >= 10 and seen["cand_gap"] >= 1


def test_zero_demand_and_all_negative_costs():
    out = run(d([5, 3], [2, 2], 0))
    assert out["multiplier"] == "0" and out["dual_value"] == "0" and out["optimum_value"] == 0
    assert out["relaxed_assignment"] == [0, 0] and out["relaxed_feasible"] is True and out["integrality_gap"] == "0"
    out = run(d([-5, -3], [2, 2], 3))
    assert out["optimum_value"] == -8 and out["dual_value"] == "-8" and out["primal_candidate"] == [1, 1]


def test_smallest_maximizing_multiplier_is_reported():
    # equal cost per weight on all items: L is flat after the breakpoint, report the smallest lam attaining the max
    out = run(d([4, 4], [2, 2], 2))
    assert out["multiplier"] == "2" and out["dual_value"] == "4"
    assert run(d([4, 4], [2, 2], 4))["multiplier"] == "2"


def test_tie_breaking_of_the_optimum_is_lexicographically_smallest():
    out = run(d([3, 3], [1, 1], 1))
    assert out["optimum_assignment"] == [0, 1] and out["optimum_value"] == 3
    # the repair heuristic takes the lowest index among equal ratios, so the candidate differs from the optimum
    assert out["primal_candidate"] == [1, 0] and out["candidate_gap"] == 0 and out["multiplier"] == "3"


def test_repair_order_is_cost_per_weight_then_index():
    out = run(d([9, 4, 4], [3, 2, 2], 4))
    assert out["multiplier"] == "2" and out["relaxed_assignment"] == [0, 0, 0]
    assert out["primal_candidate"] == [0, 1, 1] and out["primal_candidate_value"] == 8
    # equal ratios: lowest index first, so the candidate is feasible but 2 above the optimum
    out = run(d([6, 4, 4], [3, 2, 2], 4))
    assert out["primal_candidate"] == [1, 1, 0] and out["primal_candidate_value"] == 10
    assert out["optimum_assignment"] == [0, 1, 1] and out["candidate_gap"] == 2


def test_constants_and_caps():
    assert (m.MIN_N, m.MAX_N, m.MAX_COST, m.MAX_WEIGHT) == (1, 12, 100, 100)
    run(d([100] * 12, [100] * 12, 1200))
    run(d([-100], [1], 1))
    run(d([1], [100], 100))
    run(d([1], [1], 0))
    bad(d([1] * 13, [1] * 13, 1), "costs length out of range")
    bad(d([], [], 0), "costs length out of range")
    bad(d([101], [1], 1), "cost out of range")
    bad(d([-101], [1], 1), "cost out of range")
    bad(d([1], [0], 0), "weight out of range")
    bad(d([1], [101], 1), "weight out of range")
    bad(d([1], [1], -1), "demand out of range")
    bad(d([1], [1], 10 ** 6 + 1), "demand out of range")
    bad(d([1], [1], 10 ** 6), "demand exceeds total weight")
    bad(d([1, 2], [3, 4], 8), "demand exceeds total weight")
    bad(d([1], [1], 2), "demand exceeds total weight")
    bad(d([1, 2], [1]), "weights and costs must have the same length")


def test_caps_checked_before_scans():
    bad(d(["x"] * 13, [1] * 13, 1), "costs length out of range")
    bad({"costs": [None] * 13, "weights": [1], "demand": "z"}, "costs length out of range")
    bad(d([1], [1], 10 ** 9), "demand out of range")


def test_nonbool_fixtures():
    for v in (True, False, 1.0, "1", None, [1]):
        bad(d([v], [1], 0), "cost must be an int")
        bad(d([1], [v], 0), "weight must be an int")
        bad(d([1], [1], v), "demand must be an int")
    for cs, ws in (("ab", [1]), ([1], (1,)), ((1,), [1]), (None, [1]), ([1], 5)):
        bad({"costs": cs, "weights": ws, "demand": 0}, "costs and weights must be lists")


def test_key_set_errors():
    bad([], KEYS)
    bad(None, KEYS)
    bad({}, KEYS)
    bad(d() | {"x": 1}, KEYS)
    x = d()
    del x["demand"]
    bad(x, KEYS)


def test_claim_flags_and_purity():
    out = run(d())
    assert out["claims"] == {"candidate_optimal": False, "bound_tight": False,
                             "models_real_decision": False, "real_world": False}
    out["claims"]["bound_tight"] = True
    out["not_claimed"].append("x")
    again = run(d())
    assert again["claims"]["bound_tight"] is False and again["not_claimed"] == list(m.NOT_CLAIMED)
    assert len(m.NOT_CLAIMED) == 4 and "Not claimed:" in m.__doc__
    x = d([1, 2, 3], [1, 2, 3], 3)
    y = copy.deepcopy(x)
    assert run(x) == run(x) and x == y


def test_no_float_in_output():
    out = run(d([3, 9, 1], [2, 5, 7], 6))

    def walk(v):
        assert not isinstance(v, float)
        if isinstance(v, dict):
            [walk(q) for q in v.values()]
        elif isinstance(v, list):
            [walk(q) for q in v]
    walk(out)
