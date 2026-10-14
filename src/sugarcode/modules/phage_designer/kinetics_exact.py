"""Cancellation-free, validated phage kinetics (unit 68 additive repair).

``core.escape_probability`` (core.py line 75) and ``core.adsorption_kinetics``
(line 70) compute ``1 - math.exp(-x)``. For small x that rounds to exactly 0.0
(``escape_probability(1e-30, 1, 1)`` returns 0.0; the true value is 1e-30), and
neither range-checks its inputs (a negative mutation rate returns a negative
"probability"; NaN passes). This module uses ``-expm1(-x)`` and validates.

Also reported, not fixed here: core.design_fiber line 30 lacks the ``f`` prefix,
so the engineering step prints the literal text "{host_pathogen}".

Scope: Poisson and binomial escape-probability formulas for independent
single-hit trials, and first-order adsorption. Both are textbook idealisations
with one shared rate; they are not host-range or efficacy predictions.
"""
from __future__ import annotations

import math
from fractions import Fraction

CAP = 1e30
MAX_SITES = 10**9


def _num(v, name, hi=CAP):
    if isinstance(v, bool):
        raise ValueError(f"{name} must be a number, not bool")
    if not isinstance(v, (int, float)):
        raise ValueError(f"{name} must be a real number")
    if abs(v) > hi:
        raise ValueError(f"{name} magnitude exceeds {hi:g}")
    if not math.isfinite(v):
        raise ValueError(f"{name} must be finite")
    if v < 0:
        raise ValueError(f"{name} must be non-negative")
    return v


def escape_probability_exact(mutation_rate, target_sites, population) -> dict:
    """P(at least one escape variant): Poisson, and binomial when the population N is an integer.

    The binomial value is None unless ``population`` is an integer (or an integer-valued float);
    L*N being an integer is not enough. ``mu*L*N`` is formed exactly (Fraction) and rounded once.
    """
    mu = float(_num(mutation_rate, "mutation_rate", 1.0))
    if isinstance(target_sites, bool) or not isinstance(target_sites, int):
        raise ValueError("target_sites must be an integer")
    if not 1 <= target_sites <= MAX_SITES:
        raise ValueError(f"target_sites must be in [1, {MAX_SITES}]")
    pop = _num(population, "population")
    x = float(Fraction(mu) * target_sites * Fraction(pop))
    poisson = -math.expm1(-x)
    binom = None
    if isinstance(pop, int) or float(pop).is_integer():
        n = target_sites * int(pop)
        if n == 0 or mu == 0.0:
            binom = 0.0
        elif mu == 1.0:
            binom = 1.0
        else:
            binom = -math.expm1(n * math.log1p(-mu))
    return {
        "escape_probability_poisson": poisson,
        "escape_probability_binomial": binom,
        "expected_escape_variants": x,
        "model": "1-exp(-mu*L*N) via expm1; binomial 1-(1-mu)^(L*N) via log1p "
             "when population N is an integer (otherwise binomial is None)",
    }


def adsorption_exact(phage, bacteria, k_ads, time_min=60) -> dict:
    """First-order adsorption bound = P0*(1-exp(-k*B*t)) without cancellation."""
    p0 = _num(phage, "phage")
    if p0 <= 0:
        raise ValueError("phage must be positive")
    b = _num(bacteria, "bacteria")
    k = _num(k_ads, "k_ads")
    t = _num(time_min, "time_min")
    # k*b*t and P0*fraction are formed exactly (Fraction) and rounded once: left-to-right float
    # products flush e.g. 1e-30*1e-300 to 0 before the 1e30 factor can restore it.
    x = float(Fraction(k) * Fraction(b) * Fraction(t)) if (b and k and t) else 0.0
    frac = -math.expm1(-x)
    bound = float(Fraction(p0) * Fraction(frac))
    return {"bound": bound, "free": float(p0) - bound, "adsorbed_fraction": frac,
            "time_min": t, "model": "first-order adsorption, bound=P0*(-expm1(-k*B*t))"}
