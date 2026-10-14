"""Unit 68 repair pins (PARTIAL): intermediate-product underflow, binomial metadata scope, wrapper boundaries.

Oracles: Fraction/Decimal exact arithmetic (independent of the module's code path) and hand-derived literals.
Caps in the wrapper boundary tests are the module's own constants, not spec values.
"""
import math
from decimal import Decimal as D, getcontext
from fractions import Fraction

import pytest

from sugarcode.modules.phage_designer import core, hardened as h, kinetics_exact as kx

getcontext().prec = 80
NAN, INF = float("nan"), float("inf")


def rel(a, b, tol=1e-14):
    return abs(D(a) - b) <= D(tol) * abs(b)


# ---- defect 1: k*b*t must be formed exactly before rounding ----
def test_adsorption_tiny_exponent_is_not_flushed_to_zero():
    r = kx.adsorption_exact(1, 1e-30, 1e-300, 1e30)
    x = D(1e-30) * D(1e-300) * D(1e30)           # exact product of the three doubles, ~1e-300
    assert rel(r["adsorbed_fraction"], x)         # 1 - exp(-x) = x to 300 digits
    assert rel(r["bound"], x)
    assert r["adsorbed_fraction"] > 0 and r["bound"] > 0
    assert r["free"] == 1.0                       # 1 - 1e-300 rounds to 1.0


@pytest.mark.parametrize("k,b,t", [(1e-300, 1e-30, 1e30), (1e-200, 1e-100, 1e30), (1e-160, 1e-160, 1e-1), (3e-310, 1.0, 2.0)])
def test_adsorption_matches_exact_product_grid(k, b, t):
    x = D(k) * D(b) * D(t)
    r = kx.adsorption_exact(2.0, b, k, t)
    if x >= D("1e-320"):
        assert rel(r["adsorbed_fraction"], x, 1e-12)
        assert rel(r["bound"], 2 * x, 1e-12)
    else:  # 1e-160*1e-160*0.1 underflows even exactly: the true value is not representable
        assert r["adsorbed_fraction"] == float(x)


def test_adsorption_bound_is_one_rounding_of_p0_times_fraction():
    # P0=1e-300, fraction=1e-300 -> exact product 1e-600 underflows to 0.0 (the true value is not representable)
    r = kx.adsorption_exact(1e-300, 1.0, 1e-300, 1.0)
    assert r["adsorbed_fraction"] == pytest.approx(1e-300, rel=1e-14)
    assert r["bound"] == 0.0


@pytest.mark.parametrize("mu,L,N", [(1e-300, 1, 1e-30), (1e-200, 1, 1e-120), (1e-160, 3, 1e-150)])
def test_escape_tiny_expected_variants_exact_product(mu, L, N):
    x = D(mu) * L * D(N)
    r = kx.escape_probability_exact(mu, L, N)
    if x >= D("1e-320"):
        assert rel(r["expected_escape_variants"], x, 1e-12)
        assert rel(r["escape_probability_poisson"], x, 1e-12)
    else:
        assert r["expected_escape_variants"] == float(x)


def test_escape_subnormal_product_is_single_rounded():
    mu = 5e-324                                    # 2**-1074
    for L, N in [(3, 1.0), (3, 0.5), (1, 1.5), (7, 0.25)]:
        want = float(Fraction(mu) * L * Fraction(N))
        assert kx.escape_probability_exact(mu, L, N)["expected_escape_variants"] == want
    # explicit literals: 3 * 2**-1074 exact; 1.5 * 2**-1074 ties to even = 2 * 2**-1074; 7/4 -> 2 * 2**-1074
    assert kx.escape_probability_exact(mu, 3, 1.0)["expected_escape_variants"] == 3 * 2.0 ** -1074
    assert kx.escape_probability_exact(mu, 1, 1.5)["expected_escape_variants"] == 2 * 2.0 ** -1074
    assert kx.escape_probability_exact(mu, 7, 0.25)["expected_escape_variants"] == 2 * 2.0 ** -1074


# ---- defect 2: binomial metadata scope (integer-valued population N) ----
def test_binomial_requires_integer_population_not_integer_L_times_N():
    r = kx.escape_probability_exact(0.3, 2, 0.5)       # L*N = 1 is an integer but N is not
    assert r["escape_probability_binomial"] is None
    assert r["escape_probability_poisson"] == pytest.approx(float(1 - D(-(D(0.3) * 2 * D(0.5))).exp()), rel=1e-14)
    assert "population N is an integer" in r["model"]
    assert "when L*N is an integer" not in r["model"]
    ok = kx.escape_probability_exact(0.5, 3, 2)         # integer N: 1 - (1/2)**6 = 63/64
    assert ok["escape_probability_binomial"] == 63 / 64
    ok2 = kx.escape_probability_exact(0.5, 3, 2.0)      # integer-valued float N counts as an integer population
    assert ok2["escape_probability_binomial"] == 63 / 64
    assert kx.escape_probability_exact(0.5, 3, 2.5)["escape_probability_binomial"] is None


def test_model_text_is_exact_and_docstring_states_scope():
    r = kx.escape_probability_exact(0.5, 1, 1)
    assert r["model"] == ("1-exp(-mu*L*N) via expm1; binomial 1-(1-mu)^(L*N) via log1p "
                          "when population N is an integer (otherwise binomial is None)")
    assert "population" in kx.escape_probability_exact.__doc__ and "integer" in kx.escape_probability_exact.__doc__


def test_zero_population_binomial_is_zero_even_when_mutation_rate_is_one():
    # N = 0 -> L*N = 0 trials -> P(at least one escape) = 0 for every mu, including mu = 1
    for mu in (0.0, 0.25, 1.0):
        r = kx.escape_probability_exact(mu, 5, 0)
        assert r["escape_probability_binomial"] == 0.0 and r["escape_probability_poisson"] == 0.0
        assert kx.escape_probability_exact(mu, 5, 0.0)["escape_probability_binomial"] == 0.0
