"""Independent oracles for kinetics_exact. Expected values come from 50-digit Decimal / exact Fraction arithmetic
written here (no module helper reused) plus hand-derived literals. Textbook idealised kinetics only."""
import math
from decimal import Decimal, localcontext
from fractions import Fraction

import pytest
from sugarcode.modules.phage_designer import kinetics_exact as kx

@pytest.fixture(autouse=True)
def decimal_oracle_context():
    with localcontext() as context:
        context.prec = 60
        yield


def one_minus_exp_neg(x):
    return float(Decimal(1) - (-Decimal(x)).exp())


def binom_oracle(mu, n):
    """1-(1-mu)^n via exact Fraction for small n, Decimal ln for large n."""
    if n <= 2000:
        return float(1 - (1 - Fraction(mu)) ** n)
    return float(1 - ((Decimal(1) - Decimal(mu)).ln() * n).exp())


def rel(a, b, tol=1e-13):
    return a == pytest.approx(b, rel=tol, abs=0)


# ---------------- escape probability ----------------
def test_tiny_rate_does_not_cancel_to_zero():
    r = kx.escape_probability_exact(1e-30, 1, 1)
    assert r["escape_probability_poisson"] == pytest.approx(1e-30, rel=1e-15)
    assert r["escape_probability_binomial"] == pytest.approx(1e-30, rel=1e-15)
    assert r["expected_escape_variants"] == 1e-30


def test_hand_derived_half_rate_two_sites_three_cells():
    r = kx.escape_probability_exact(0.5, 2, 3)
    # x = .5*2*3 = 3 ; poisson 1-e^-3 ; n = 6, binomial 1-(1/2)^6 = 63/64 exactly
    assert r["expected_escape_variants"] == 3.0
    assert r["escape_probability_binomial"] == 63 / 64
    assert rel(r["escape_probability_poisson"], one_minus_exp_neg(3))
    assert r["escape_probability_poisson"] == pytest.approx(0.950212931632136, rel=1e-14)


@pytest.mark.parametrize("mu,L,N", [(0.1, 10, 10), (1e-3, 3, 1000), (0.25, 1, 7), (1e-9, 5, 10**6), (0.999, 1, 2), (1e-6, 1000, 1000)])
def test_poisson_and_binomial_match_independent_oracle(mu, L, N):
    r = kx.escape_probability_exact(mu, L, N)
    x = mu * L * N
    assert rel(r["escape_probability_poisson"], float(Decimal(1) - (-Decimal(mu) * L * N).exp()))
    assert rel(r["escape_probability_binomial"], binom_oracle(mu, L * N))
    assert r["expected_escape_variants"] == pytest.approx(x, rel=1e-15)
    assert r["escape_probability_binomial"] <= 1.0 and r["escape_probability_poisson"] <= 1.0


def test_huge_trial_count_binomial_uses_log1p():
    # mu=1e-20, n=1e20 -> 1-(1-1e-20)^(1e20) = 0.63212055882855767840 to 20 digits (1-1/e)
    r = kx.escape_probability_exact(1e-20, 1, 10 ** 20)
    assert r["escape_probability_binomial"] == pytest.approx(0.6321205588285577, rel=1e-13)
    assert r["escape_probability_poisson"] == pytest.approx(0.6321205588285577, rel=1e-13)


def test_binomial_none_for_non_integer_population_but_integer_valued_float_ok():
    assert kx.escape_probability_exact(0.3, 1, 2.5)["escape_probability_binomial"] is None
    r = kx.escape_probability_exact(0.5, 1, 4.0)
    assert r["escape_probability_binomial"] == 15 / 16                       # 1 - .5^4


def test_zero_cases_and_certainty():
    z = kx.escape_probability_exact(0.0, 3, 10)
    assert z["escape_probability_poisson"] == 0.0 and z["escape_probability_binomial"] == 0.0 and z["expected_escape_variants"] == 0.0
    p = kx.escape_probability_exact(0.3, 3, 0)
    assert p["escape_probability_poisson"] == 0.0 and p["escape_probability_binomial"] == 0.0
    assert kx.escape_probability_exact(1.0, 1, 3)["escape_probability_binomial"] == 1.0
    assert kx.escape_probability_exact(1.0, 1, 3)["escape_probability_poisson"] == pytest.approx(1 - math.exp(-3), rel=1e-15)


def test_saturation_large_exposure():
    r = kx.escape_probability_exact(0.5, 10 ** 9, 10 ** 30)          # n = 1e39, x = 5e38
    assert r["escape_probability_poisson"] == 1.0 and r["escape_probability_binomial"] == 1.0


def test_single_trial_binomial_equals_rate():
    for mu in (1e-300, 1e-10, 0.3, 0.9999999):
        assert kx.escape_probability_exact(mu, 1, 1)["escape_probability_binomial"] == pytest.approx(mu, rel=1e-14)


@pytest.mark.parametrize("mu", [-1e-300, -1, float("nan"), float("inf"), float("-inf"), math.nextafter(1.0, 2), 2, True, False, "0.1", None, 1j, [0.1]])
def test_bad_mutation_rate(mu):
    with pytest.raises(ValueError):
        kx.escape_probability_exact(mu, 1, 1)


def test_mutation_rate_error_messages_name_the_cause():
    with pytest.raises(ValueError, match="mutation_rate must be a number, not bool"):
        kx.escape_probability_exact(True, 1, 1)
    with pytest.raises(ValueError, match="mutation_rate must be a real number"):
        kx.escape_probability_exact("1", 1, 1)
    with pytest.raises(ValueError, match="mutation_rate magnitude exceeds"):
        kx.escape_probability_exact(1.5, 1, 1)
    with pytest.raises(ValueError, match="mutation_rate must be finite"):
        kx.escape_probability_exact(float("nan"), 1, 1)
    with pytest.raises(ValueError, match="mutation_rate must be non-negative"):
        kx.escape_probability_exact(-0.1, 1, 1)
    assert kx.escape_probability_exact(1.0, 1, 1)["escape_probability_binomial"] == 1.0         # edge accepted


@pytest.mark.parametrize("L", [0, -1, 10 ** 9 + 1, 1.0, 2.5, True, False, "1", None, float("nan")])
def test_bad_target_sites(L):
    with pytest.raises(ValueError):
        kx.escape_probability_exact(0.1, L, 1)


def test_target_sites_edges():
    assert kx.escape_probability_exact(1e-30, 1, 1)["expected_escape_variants"] == 1e-30
    assert kx.escape_probability_exact(1e-30, 10 ** 9, 1)["expected_escape_variants"] == pytest.approx(1e-21, rel=1e-14)


@pytest.mark.parametrize("N", [-1, -1e-300, float("nan"), float("inf"), math.nextafter(1e30, math.inf), 10 ** 31, True, "1", None])
def test_bad_population(N):
    with pytest.raises(ValueError):
        kx.escape_probability_exact(0.1, 1, N)


def test_population_cap_edge_accepted():
    assert kx.escape_probability_exact(1e-40, 1, 1e30)["expected_escape_variants"] == pytest.approx(1e-10, rel=1e-14)
    assert kx.escape_probability_exact(1e-40, 1, 10 ** 30)["escape_probability_binomial"] == pytest.approx(1e-10, rel=1e-6)


def test_model_text_present():
    assert "expm1" in kx.escape_probability_exact(0.1, 1, 1)["model"]


# ---------------- adsorption ----------------
def test_adsorption_hand_derived_default_time():
    r = kx.adsorption_exact(100.0, 1.0, 0.01)
    # frac = 1 - e^-0.6 = 0.45118836390597361 (60 min default)
    assert r["time_min"] == 60
    assert r["adsorbed_fraction"] == pytest.approx(0.4511883639059736, rel=1e-14)
    assert r["bound"] == pytest.approx(45.11883639059736, rel=1e-14)
    assert r["free"] == pytest.approx(54.88116360940264, rel=1e-14)
    assert r["bound"] + r["free"] == pytest.approx(100.0, rel=1e-15)


@pytest.mark.parametrize("P,B,k,t", [(1e6, 1e8, 1e-9, 10), (5.0, 2.0, 0.003, 7.5), (1e-5, 1e3, 1e-12, 100), (3.0, 1.0, 1.0, 30)])
def test_adsorption_matches_decimal_oracle(P, B, k, t):
    r = kx.adsorption_exact(P, B, k, t)
    frac = float(Decimal(1) - (-(Decimal(k) * Decimal(B) * Decimal(t))).exp())
    assert rel(r["adsorbed_fraction"], frac)
    assert rel(r["bound"], float(Decimal(P) * (Decimal(1) - (-(Decimal(k) * Decimal(B) * Decimal(t))).exp())))
    assert r["time_min"] == t


def test_adsorption_tiny_exponent_no_cancellation():
    r = kx.adsorption_exact(1.0, 1.0, 1e-30, 1.0)
    assert r["bound"] == pytest.approx(1e-30, rel=1e-15) and r["free"] == 1.0 - r["bound"]


def test_adsorption_fractional_phage_and_zero_factors():
    assert kx.adsorption_exact(0.5, 1.0, 1.0, 1.0)["bound"] == pytest.approx(0.5 * (1 - math.exp(-1)), rel=1e-14)
    for args in [(2.0, 0, 1.0, 1.0), (2.0, 1.0, 0, 1.0), (2.0, 1.0, 1.0, 0), (2.0, 0.0, 0.0, 0.0)]:
        r = kx.adsorption_exact(*args)
        assert r["bound"] == 0.0 and r["free"] == 2.0 and r["adsorbed_fraction"] == 0.0


def test_adsorption_saturation_and_integer_inputs():
    r = kx.adsorption_exact(10, 10 ** 10, 1, 60)
    assert r["adsorbed_fraction"] == 1.0 and r["bound"] == 10.0 and r["free"] == 0.0


@pytest.mark.parametrize("args", [(0, 1, 1, 1), (0.0, 1, 1, 1), (-1, 1, 1, 1), (1, -1, 1, 1), (1, 1, -1, 1), (1, 1, 1, -1),
                                  (float("nan"), 1, 1, 1), (1, float("nan"), 1, 1), (1, 1, float("inf"), 1), (1, 1, 1, float("inf")),
                                  (True, 1, 1, 1), (1, True, 1, 1), (1, 1, True, 1), (1, 1, 1, True),
                                  ("1", 1, 1, 1), (None, 1, 1, 1), (1, None, 1, 1), (1, 1, None, 1), (1, 1, 1, None), (1j, 1, 1, 1)])
def test_adsorption_bad_arguments(args):
    with pytest.raises(ValueError):
        kx.adsorption_exact(*args)


def test_adsorption_messages_and_cap_edges():
    with pytest.raises(ValueError, match="phage must be positive"):
        kx.adsorption_exact(0, 1, 1, 1)
    for name, pos in (("phage", 0), ("bacteria", 1), ("k_ads", 2), ("time_min", 3)):
        args = [1.0, 1.0, 1e-30, 1.0]
        args[pos] = math.nextafter(1e30, math.inf)
        with pytest.raises(ValueError, match=f"{name} magnitude exceeds"):
            kx.adsorption_exact(*args)
        args[pos] = 1e30 if name != "k_ads" else 1e-30
        assert kx.adsorption_exact(*args)["bound"] >= 0.0
    with pytest.raises(ValueError, match="bacteria must be non-negative"):
        kx.adsorption_exact(1, -1, 1, 1)
    assert kx.adsorption_exact(1e30, 1.0, 1e-30, 1.0)["bound"] == pytest.approx(1.0, rel=1e-14)
