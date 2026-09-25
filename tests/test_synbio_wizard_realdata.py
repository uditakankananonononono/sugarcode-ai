"""Module 122 synbio_wizard: SSA truncation honesty and codon-table contracts,
with kinetic identities against the module's own closed forms."""
import pytest
from sugarcode.modules.synbio_wizard import (gillespie_expression, variant_effect,
                                             flux_balance, deterministic_expression,
                                             evolutionary_stability)


def test_gillespie_truncation_is_reported():
    r = gillespie_expression(hours=24, transcription=10, translation=1000, seed=1)
    assert r["truncated"] is True and r["simulated_hours"] < 11  # 10.69 measured
    assert r["hours"] == 24  # requested horizon kept, actual horizon now explicit
    r2 = gillespie_expression(hours=2, seed=3)
    assert r2["truncated"] is False and r2["simulated_hours"] >= 2


def test_invalid_codon_rejected():
    with pytest.raises(ValueError):
        variant_effect("ZZZ", "QQQ")  # was: silently "synonymous", deleterious 0.5
    with pytest.raises(ValueError):
        variant_effect("GCT", "ZZZ")  # was: silently "missense"


def test_valid_variant_classes_unchanged():
    assert variant_effect("ATG", "TGA")["class"] == "stop_gain"
    assert variant_effect("TGG", "TGA", .9, True)["deleterious_probability"] > .8


def test_flux_balance_respects_limits():
    r = flux_balance(["a", "b", "c", "d"])
    assert r["product_flux_mmol_gdw_h"] > 0
    assert r["atp_use"] <= 20 + 1e-9 and r["redox_use"] <= 12 + 1e-9
    f = list(r["fluxes_mmol_gdw_h"].values())
    assert all(f[i + 1] <= f[i] + 1e-9 for i in range(len(f) - 1))  # serial pathway


def test_expression_and_stability_identities():
    r = deterministic_expression(hours=100)
    assert r["protein"][-1] == pytest.approx(r["steady_protein"], rel=.01)  # 40.0
    e = evolutionary_stability(generations=100, mutation_rate=1e-6, burden=.1, selection=.02)
    assert e["functional_fraction"] == pytest.approx((1 - 1e-6) ** 100 * 2.718281828459045 ** (-.08 * 100), rel=1e-6)
