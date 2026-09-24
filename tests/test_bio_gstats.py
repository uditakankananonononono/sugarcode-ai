"""bio.gstats genetics statistics toolkit (drop 81)."""
import math
import random
from math import lgamma

import pytest

from sugarcode.bio import gstats as gs


def _hwe_brute(n_aa, n_ab, n_bb):
    """Independent oracle: direct hypergeometric enumeration of the
    heterozygote-count distribution (NOT the Wigginton recurrence)."""
    n = n_aa + n_ab + n_bb
    rare = 2 * min(n_aa, n_bb) + n_ab
    common = 2 * n - rare

    def p(h):
        hr, hc = (rare - h) // 2, (common - h) // 2
        if hr < 0 or hc < 0:
            return 0.0
        return math.exp(h * math.log(2) + lgamma(n + 1) + lgamma(rare + 1)
                        + lgamma(common + 1) - lgamma(2 * n + 1)
                        - lgamma(hr + 1) - lgamma(h + 1) - lgamma(hc + 1))

    ps = {h: p(h) for h in range(rare % 2, rare + 1, 2)}
    tot = sum(ps.values())
    obs = ps[n_ab]
    return min(1.0, sum(x for x in ps.values()
                        if x <= obs * (1 + 1e-12)) / tot)


def test_hwe_hand_computed():
    # (2,2,0): P(h=2)=6/7, P(h=0)=1/7; observed is the mode -> p = 1
    assert gs.hwe_exact(2, 2, 0) == pytest.approx(1.0)
    # (3,0,1): only h=0 is <= observed probability -> p = 1/7
    assert gs.hwe_exact(3, 0, 1) == pytest.approx(1 / 7)
    # single heterozygote: only one configuration exists -> p = 1
    assert gs.hwe_exact(0, 1, 0) == pytest.approx(1.0)


def test_hwe_brute_force_oracle():
    random.seed(7)
    worst = 0.0
    for _ in range(500):
        c = [random.randint(0, 15) for _ in range(3)]
        if sum(c) == 0:
            continue
        worst = max(worst, abs(gs.hwe_exact(*c) - _hwe_brute(*c)))
    assert worst < 1e-9


def test_hwe_validation():
    with pytest.raises(ValueError):
        gs.hwe_exact(-1, 2, 3)
    with pytest.raises(ValueError):
        gs.hwe_exact(0, 0, 0)


def test_chi_square_2x2_hand_computed():
    r = gs.chi_square_2x2(40, 60, 50, 50)
    assert r["statistic"] == pytest.approx(200 * 1000.0**2 / 9.9e7)
    assert r["p"] == pytest.approx(math.erfc(math.sqrt(
        r["statistic"] / 2)))
    ry = gs.chi_square_2x2(40, 60, 50, 50, yates=True)
    assert ry["statistic"] == pytest.approx(200 * 900.0**2 / 9.9e7)
    assert ry["p"] > r["p"]  # Yates is conservative
    with pytest.raises(ValueError):
        gs.chi_square_2x2(0, 0, 1, 1)  # zero row margin


def test_chi2_sf_closed_forms():
    assert gs.chi2_sf(3.84, 1) == pytest.approx(0.0500435, abs=1e-6)
    assert gs.chi2_sf(5.99, 2) == pytest.approx(math.exp(-2.995), abs=1e-12)
    with pytest.raises(ValueError):
        gs.chi2_sf(1.0, 3)


def test_genotypic_test_hand_computed():
    g = gs.genotypic_test((10, 20, 30), (30, 20, 10))
    assert g["statistic"] == pytest.approx(20.0)
    assert g["p"] == pytest.approx(math.exp(-10))
    with pytest.raises(ValueError):
        gs.genotypic_test((0, 0, 0), (1, 2, 3))


def test_odds_ratio_woolf_hand_computed():
    o = gs.odds_ratio(40, 60, 50, 50)
    assert o["odds_ratio"] == pytest.approx(2 / 3)
    assert o["corrected"] is False
    se = math.sqrt(1 / 40 + 1 / 60 + 1 / 50 + 1 / 50)
    z = 1.959963985120054
    assert o["ci_low"] == pytest.approx(math.exp(math.log(2 / 3) - z * se))
    assert o["ci_high"] == pytest.approx(math.exp(math.log(2 / 3) + z * se))


def test_odds_ratio_zero_cell_haldane():
    o = gs.odds_ratio(0, 10, 5, 50)
    assert o["corrected"] is True
    assert o["odds_ratio"] == pytest.approx(0.5 * 50.5 / (10.5 * 5.5))


def test_allelic_test_allele_collapse():
    r = gs.allelic_test((10, 20, 30), (30, 20, 10))
    # case alleles: A = 2*10+20 = 40, a = 20+2*30 = 80; ctrl 80, 40
    assert r["table"] == [[40, 80], [80, 40]]
    direct = gs.chi_square_2x2(40, 80, 80, 40)
    assert r["statistic"] == pytest.approx(direct["statistic"])
    assert r["odds_ratio"] == pytest.approx(40 * 40 / (80 * 80))


def test_bonferroni_hand_computed():
    b = gs.bonferroni([0.01, 0.04, 0.20])
    assert b == pytest.approx([0.03, 0.12, 0.60])
    assert gs.bonferroni([0.5, 0.5]) == [1.0, 1.0]  # capped at 1
    with pytest.raises(ValueError):
        gs.bonferroni([1.2])


def test_bh_published_example():
    # The 15 p-values from Benjamini & Hochberg 1995's own worked example
    p = [0.0001, 0.0004, 0.0019, 0.0095, 0.0201, 0.0278, 0.0298, 0.0344,
         0.0459, 0.3240, 0.4262, 0.5719, 0.6528, 0.7590, 1.000]
    adj = gs.benjamini_hochberg(p)
    expect = [0.0015, 0.003, 0.0095, 0.035625, 0.0603, 0.0638571,
              0.0638571, 0.0645, 0.0765, 0.486, 0.5811818, 0.714875,
              0.7532308, 0.8132143, 1.0]
    assert adj == pytest.approx(expect, abs=1e-4)
    # the paper's headline: 4 rejections at FDR 0.05
    assert sum(1 for x in adj if x <= 0.05) == 4


def test_adjust_invariants():
    random.seed(1)
    for _ in range(100):
        pv = [random.random() for _ in range(random.randint(1, 20))]
        bh, bf = gs.benjamini_hochberg(pv), gs.bonferroni(pv)
        assert all(a >= p - 1e-15 for a, p in zip(bh, pv))   # BH >= raw
        assert all(b <= f + 1e-15 for b, f in zip(bh, bf))   # BH <= Bonf
        assert all(0 <= a <= 1 for a in bh + bf)
    assert gs.benjamini_hochberg([]) == []
    with pytest.raises(ValueError):
        gs.benjamini_hochberg([-0.1])
