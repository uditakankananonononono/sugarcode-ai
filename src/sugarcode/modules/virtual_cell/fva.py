"""Additive: flux variability analysis (FVA) for virtual_cell.

core.py fba()/pfba() return ONE optimum (`res.x` from linprog) although FBA optima are
degenerate (its own pfba docstring says so); no function reports which fluxes are fixed,
free or blocked at the optimum. FVA: for each reaction, min and max of v subject to
S v = 0, lb <= v <= ub, objective >= fraction * optimum (two LPs per reaction).

Tolerance wording: `fixed` is hi - lo <= tol. With tol=0 it is True only when the min LP and the max
LP return bit-for-bit identical values; solver float noise (~1e-15) can make a truly fixed reaction
report fixed=False at tol=0. Use the default tol=1e-6 for practical fixed detection."""
from __future__ import annotations
import math
import numpy as np
from scipy.optimize import linprog

MAX_REACTIONS = 2000


def _num(v, name):
    if isinstance(v, bool) or not isinstance(v, (int, float, np.floating, np.integer)):
        raise TypeError(f"{name} must be a real number")
    if isinstance(v, int) and abs(v) > 10**12:
        raise ValueError(f"{name} out of range")
    f = float(v)
    if not math.isfinite(f) or abs(f) > 1e12:
        raise ValueError(f"{name} must be finite and below 1e12")
    return f


def flux_variability(model, objective=None, fraction_of_optimum=1.0, bounds_override=None, tol=1e-6):
    for attr in ("S", "lb", "ub", "reactions", "metabolites", "objective"):
        if not hasattr(model, attr):
            raise TypeError("model must be a MetabolicModel")
    n = len(model.reactions)
    if n < 1 or n > MAX_REACTIONS:
        raise ValueError(f"model needs 1..{MAX_REACTIONS} reactions")
    S = np.asarray(model.S, float)
    if S.shape != (len(model.metabolites), n) or not np.all(np.isfinite(S)):
        raise ValueError("S must be finite with shape (metabolites, reactions)")
    lb = np.asarray(model.lb, float).copy(); ub = np.asarray(model.ub, float).copy()
    if lb.shape != (n,) or ub.shape != (n,) or not (np.all(np.isfinite(lb)) and np.all(np.isfinite(ub))):
        raise ValueError("lb/ub must be finite vectors, one per reaction")
    f = _num(fraction_of_optimum, "fraction_of_optimum")
    if not 0.0 <= f <= 1.0:
        raise ValueError("fraction_of_optimum must be in [0, 1]")
    tol = _num(tol, "tol")
    if tol < 0:
        raise ValueError("tol must be >= 0")
    obj = objective or model.objective
    if obj not in model.reactions:
        raise ValueError(f"unknown objective reaction {obj!r}")
    if bounds_override is not None:
        if not isinstance(bounds_override, dict):
            raise TypeError("bounds_override must be a dict")
        for name, pair in bounds_override.items():
            if name not in model.reactions:
                raise ValueError(f"unknown reaction {name!r} in bounds_override")
            if not isinstance(pair, (tuple, list)) or len(pair) != 2:
                raise ValueError("bounds must be (lo, hi)")
            i = model.reactions.index(name); lb[i], ub[i] = _num(pair[0], "lower bound"), _num(pair[1], "upper bound")
    if np.any(lb > ub):
        raise ValueError("a lower bound exceeds its upper bound")
    oi = model.reactions.index(obj)
    beq = np.zeros(len(model.metabolites))
    c = np.zeros(n); c[oi] = -1.0
    base = linprog(c, A_eq=S, b_eq=beq, bounds=list(zip(lb, ub)), method="highs")
    note = ("PARTIAL: LP-based flux variability of the module's toy stoichiometric models; "
            "objective constraint is objective >= optimum - (1 - fraction) * |optimum| "
            "(equals fraction * optimum when optimum >= 0); "
            "no genome-scale network, no gene-protein-reaction rules, no wet-lab claim")
    if not base.success:
        return {"status": "infeasible", "objective": obj, "optimum": None, "objective_bound": None, "ranges": {}, "status_note": note}
    opt = float(-base.fun)
    bound = opt - (1.0 - f) * abs(opt)  # = f*opt when opt >= 0; stays <= opt when opt < 0
    # The objective floor is applied EXACTLY (so reported min/max are the true bounds and tol=0 can give
    # fixed=True). A 1e-9*max(1,|opt|) relaxation is used only as a fallback if an LP fails with the exact floor.
    lb2 = lb.copy(); lb2[oi] = max(lb2[oi], bound)
    lb3 = lb.copy(); lb3[oi] = max(lb3[oi], bound - 1e-9 * max(1.0, abs(opt)))
    ranges = {}
    for i, name in enumerate(model.reactions):
        vals = []
        for sign in (1.0, -1.0):  # minimise v, then minimise -v (= maximise v)
            ci = np.zeros(n); ci[i] = sign
            r = linprog(ci, A_eq=S, b_eq=beq, bounds=list(zip(lb2, ub)), method="highs")
            if not r.success:
                r = linprog(ci, A_eq=S, b_eq=beq, bounds=list(zip(lb3, ub)), method="highs")
            if not r.success:
                raise ValueError(f"FVA LP failed for {name}: {r.message}")
            vals.append(float(r.x[i]))
        lo, hi = vals
        ranges[name] = {"min": lo, "max": hi, "fixed": bool(hi - lo <= tol),
                        "blocked": bool(abs(lo) <= tol and abs(hi) <= tol)}
    return {"status": "optimal", "objective": obj, "optimum": opt, "fraction_of_optimum": f,
            "objective_bound": bound, "ranges": ranges, "status_note": note}
