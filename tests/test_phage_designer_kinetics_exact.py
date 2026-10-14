"""Tests for phage_designer.kinetics_exact (unit 68 additive repair).

Oracle: decimal.Decimal at 80 digits (independent exp / power), not the
module's expm1/log1p code path.
"""
import math
from decimal import Decimal, localcontext

import pytest

from sugarcode.modules.phage_designer import core
from sugarcode.modules.phage_designer import kinetics_exact as kx

@pytest.fixture(autouse=True)
def decimal_oracle_context():
    with localcontext() as context:
        context.prec = 80
        yield


def d_one_minus_exp_neg(x):
    return Decimal(1) - (-Decimal(x)).exp()


def d_binomial_escape(mu, n):
    return Decimal(1) - (Decimal(1) - Decimal(mu)) ** int(n)


def test_old_functions_lose_small_probabilities():
    """Characterises core.escape_probability / adsorption_kinetics `1-exp(-x)`."""
    assert core.escape_probability(1e-30, 1, 1)["escape_probability"] == 0.0
    assert core.adsorption_kinetics(1.0, 1e-9, 1e-9, 1)["adsorbed_fraction"] == 0.0   # true value 1e-18
    assert core.escape_probability(-1e-8, 1, 1e8)["escape_probability"] < 0


@pytest.mark.parametrize("mu,sites,pop", [
    (1e-30, 1, 1), (1e-20, 3, 1e3), (1e-8, 1, 1e8), (3e-9, 2, 5e7), (1e-5, 10, 1e6), (0.5, 1, 40),
])
def test_poisson_escape_matches_decimal(mu, sites, pop):
    got = kx.escape_probability_exact(mu, sites, pop)["escape_probability_poisson"]
    want = d_one_minus_exp_neg(Decimal(mu) * sites * Decimal(pop))
    assert got == pytest.approx(float(want), rel=1e-12)


@pytest.mark.parametrize("mu,sites,pop", [(1e-30, 1, 1), (1e-8, 1, 10**8), (3e-9, 2, 5 * 10**7), (0.25, 1, 7)])
def test_binomial_escape_matches_decimal(mu, sites, pop):
    got = kx.escape_probability_exact(mu, sites, pop)["escape_probability_binomial"]
    want = d_binomial_escape(Decimal(mu), sites * pop)
    assert got == pytest.approx(float(want), rel=1e-12)


def test_limits_and_monotonicity():
    z = kx.escape_probability_exact(0.0, 1, 10**6)
    assert z["escape_probability_poisson"] == 0.0 and z["escape_probability_binomial"] == 0.0
    big = kx.escape_probability_exact(1e-3, 1, 10**9)
    assert big["escape_probability_poisson"] == 1.0
    a = kx.escape_probability_exact(1e-8, 1, 10**6)["escape_probability_poisson"]
    b = kx.escape_probability_exact(1e-8, 1, 10**7)["escape_probability_poisson"]
    assert 0 < a < b < 1
    assert big["expected_escape_variants"] == pytest.approx(1e-3 * 1e9)


def test_binomial_requires_integer_trials_poisson_does_not():
    r = kx.escape_probability_exact(1e-8, 1, 2.5e7)
    assert r["escape_probability_binomial"] == pytest.approx(
        float(d_binomial_escape(Decimal(1e-8), 25_000_000)), rel=1e-12)
    r2 = kx.escape_probability_exact(1e-8, 1, 1.5)
    assert r2["escape_probability_binomial"] is None
    assert r2["escape_probability_poisson"] > 0


@pytest.mark.parametrize("p0,B,k,t", [
    (1.0, 1e-9, 1e-9, 1), (1e6, 1e8, 1e-9, 5), (50.0, 10.0, 0.01, 60), (1.0, 1e5, 1e-7, 1e-3),
])
def test_adsorption_matches_decimal(p0, B, k, t):
    r = kx.adsorption_exact(p0, B, k, t)
    want = d_one_minus_exp_neg(Decimal(k) * Decimal(B) * Decimal(t))
    assert r["adsorbed_fraction"] == pytest.approx(float(want), rel=1e-12)
    assert r["bound"] + r["free"] == pytest.approx(p0, rel=1e-12)
    assert r["bound"] == pytest.approx(float(Decimal(p0) * want), rel=1e-12)


def test_adsorption_zero_cases():
    for args in [(1.0, 0, 1.0, 1.0), (1.0, 1.0, 0, 1.0), (1.0, 1.0, 1.0, 0)]:
        r = kx.adsorption_exact(*args)
        assert r["adsorbed_fraction"] == 0.0 and r["bound"] == 0.0 and r["free"] == 1.0


BAD = [True, False, "1", None, float("nan"), float("inf"), -1.0, 10**400, -1e-300]


@pytest.mark.parametrize("bad", BAD)
def test_escape_validation(bad):
    for args in [(bad, 1, 10), (1e-8, bad, 10), (1e-8, 1, bad)]:
        with pytest.raises(ValueError):
            kx.escape_probability_exact(*args)


@pytest.mark.parametrize("bad", BAD)
def test_adsorption_validation(bad):
    for args in [(bad, 1.0, 1.0, 1.0), (1.0, bad, 1.0, 1.0), (1.0, 1.0, bad, 1.0), (1.0, 1.0, 1.0, bad)]:
        with pytest.raises(ValueError):
            kx.adsorption_exact(*args)


def test_domain_limits():
    with pytest.raises(ValueError):
        kx.escape_probability_exact(1.5, 1, 10)          # rate > 1
    with pytest.raises(ValueError):
        kx.escape_probability_exact(1e-8, 0, 10)         # zero sites
    with pytest.raises(ValueError):
        kx.escape_probability_exact(1e-8, 2.5, 10)       # fractional sites
    with pytest.raises(ValueError):
        kx.adsorption_exact(0.0, 1.0, 1.0, 1.0)          # phage must be positive (as core)
