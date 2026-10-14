"""Lagrangian Relaxation - exact dual bound for a single-demand binary cost minimization.

Pure function over caller data. No retrieval, no network, no clock, no floats, no
randomness. Problem: minimize sum(c_i x_i) over x in {0,1}^n subject to sum(a_i x_i) >= b.
Input: costs, n integers -100..100 (n from 1 to 12), weights, n integers 1..100, and demand,
an integer 0..sum(weights) (a larger demand is infeasible and refused).

The demand constraint is relaxed with a multiplier lam >= 0. The Lagrangian dual is
L(lam) = lam*b + sum(min(0, c_i - lam*a_i)). It is concave and piecewise linear, so its
maximum over lam >= 0 is at lam = 0 or at a breakpoint c_i/a_i > 0; every candidate is
evaluated as an exact Fraction and the smallest maximizing multiplier is reported. The
relaxed assignment at that multiplier takes item i when c_i - lam*a_i < 0. A primal
candidate is built from it by adding the remaining items in ascending cost per weight
(ties by index) until the demand is met. The true optimum is found by enumerating all 2^n
assignments (lexicographically smallest on ties) so the integrality gap is measured, not
assumed: optimum - dual >= 0 is reported as is and is never closed or rounded away.

Scope: PARTIAL for the Lagrangian Relaxation line. One relaxed constraint, one scalar
multiplier, exact breakpoint maximization, a repair heuristic for a primal candidate. It
does no subgradient iteration, no multiple constraints and no branch and bound.

Not claimed: that the primal candidate is optimal, that the dual bound is tight, that the
costs and weights model any real decision, or anything about the real world. Every claim
flag in the result is False.
"""
from fractions import Fraction
from itertools import product

MIN_N = 1
MAX_N = 12
MAX_COST = 100
MAX_WEIGHT = 100
_TOP = frozenset({"costs", "weights", "demand"})

NOT_CLAIMED = (
    "the primal candidate is optimal",
    "the dual bound is tight",
    "the costs and weights model a real decision",
    "real-world outcome",
)
CLAIMS = {"candidate_optimal": False, "bound_tight": False, "models_real_decision": False, "real_world": False}


class LagrangeError(ValueError):
    pass


def _int(v, lo, hi, name):
    if isinstance(v, bool) or not isinstance(v, int):
        raise LagrangeError(f"{name} must be an int")
    if v < lo or v > hi:
        raise LagrangeError(f"{name} out of range")
    return v


def _dual(lam, c, a, b):
    return lam * b + sum(min(Fraction(0), ci - lam * ai) for ci, ai in zip(c, a))


def lagrangian_relaxation(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise LagrangeError("data keys must be exactly costs, weights, demand")
    cs, ws = data["costs"], data["weights"]
    if not isinstance(cs, list) or not isinstance(ws, list):
        raise LagrangeError("costs and weights must be lists")
    if not MIN_N <= len(cs) <= MAX_N:
        raise LagrangeError("costs length out of range")
    if len(ws) != len(cs):
        raise LagrangeError("weights and costs must have the same length")
    c = [_int(v, -MAX_COST, MAX_COST, "cost") for v in cs]
    a = [_int(v, 1, MAX_WEIGHT, "weight") for v in ws]
    b = _int(data["demand"], 0, 10 ** 6, "demand")
    if b > sum(a):
        raise LagrangeError("demand exceeds total weight")
    n = len(c)

    cands = [Fraction(0)] + sorted({Fraction(ci, ai) for ci, ai in zip(c, a) if ci > 0})
    best_lam, best_val = None, None
    for lam in cands:
        v = _dual(lam, c, a, b)
        if best_val is None or v > best_val:
            best_lam, best_val = lam, v
    relaxed = [1 if Fraction(ci) - best_lam * ai < 0 else 0 for ci, ai in zip(c, a)]
    cand = list(relaxed)
    wt = sum(ai for ai, xi in zip(a, cand) if xi)
    if wt < b:
        order = sorted((i for i in range(n) if not cand[i]), key=lambda i: (Fraction(c[i], a[i]), i))
        for i in order:
            if wt >= b:
                break
            cand[i] = 1
            wt += a[i]
    cand_val = sum(ci * xi for ci, xi in zip(c, cand))

    opt_val, opt_x = None, None
    for x in product((0, 1), repeat=n):
        if sum(ai * xi for ai, xi in zip(a, x)) < b:
            continue
        v = sum(ci * xi for ci, xi in zip(c, x))
        if opt_val is None or v < opt_val:
            opt_val, opt_x = v, list(x)
    return {
        "items": n,
        "multiplier": str(best_lam),
        "dual_value": str(best_val),
        "relaxed_assignment": relaxed,
        "relaxed_weight": sum(ai for ai, xi in zip(a, relaxed) if xi),
        "relaxed_feasible": sum(ai for ai, xi in zip(a, relaxed) if xi) >= b,
        "primal_candidate": cand,
        "primal_candidate_value": cand_val,
        "optimum_value": opt_val,
        "optimum_assignment": opt_x,
        "integrality_gap": str(Fraction(opt_val) - best_val),
        "candidate_gap": cand_val - opt_val,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
