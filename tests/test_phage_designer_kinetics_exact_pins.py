"""Boundary pins from the mutation battery (unit 68 delta). Literals on purpose."""
import pytest

from sugarcode.modules.phage_designer import kinetics_exact as kx


def test_numeric_cap_literal():
    assert kx.adsorption_exact(1e30, 1.0, 1e-30, 1.0)["bound"] > 0           # at cap
    for bad in (1.0000001e30, 2e30):
        with pytest.raises(ValueError):
            kx.adsorption_exact(bad, 1.0, 1.0, 1.0)
        with pytest.raises(ValueError):
            kx.escape_probability_exact(1e-8, 1, bad)


def test_site_limit_literal():
    assert kx.escape_probability_exact(1e-30, 10**9, 1)["escape_probability_poisson"] > 0
    with pytest.raises(ValueError):
        kx.escape_probability_exact(1e-30, 10**9 + 1, 1)
    with pytest.raises(ValueError):
        kx.escape_probability_exact(1e-30, 11**9, 1)


def test_rate_above_one_rejected_even_without_binomial():
    for mu in (1.0000001, 1.5, 2.0):
        with pytest.raises(ValueError):
            kx.escape_probability_exact(mu, 1, 2.5)    # non-integer N: binomial branch skipped
    assert kx.escape_probability_exact(1.0, 1, 2.5)["escape_probability_poisson"] > 0.9


def test_zero_rate_or_zero_population_binomial_is_zero():
    assert kx.escape_probability_exact(0.0, 5, 100)["escape_probability_binomial"] == 0.0
    assert kx.escape_probability_exact(0.3, 5, 0)["escape_probability_binomial"] == 0.0
    assert kx.escape_probability_exact(1.0, 1, 3)["escape_probability_binomial"] == 1.0


def test_single_trial_binomial_is_the_rate():
    assert kx.escape_probability_exact(0.3, 1, 1)["escape_probability_binomial"] == pytest.approx(0.3, rel=1e-15)


def test_default_time_is_60_minutes():
    import math
    r = kx.adsorption_exact(1.0, 1.0, 0.01)
    assert r["time_min"] == 60
    assert r["adsorbed_fraction"] == pytest.approx(-math.expm1(-0.6), rel=1e-15)


def test_fractional_phage_below_one_accepted():
    assert kx.adsorption_exact(0.5, 1.0, 1.0, 1.0)["bound"] == pytest.approx(0.5 * (1 - 2.718281828459045 ** -1), rel=1e-12)
