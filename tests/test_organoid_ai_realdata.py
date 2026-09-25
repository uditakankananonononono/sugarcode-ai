"""Module 113 organoid_ai: curve identities and NCBI Gene-verified marker symbols."""
import pytest
from sugarcode.modules.cell_twin.core import DRUG_ACTIONS
from sugarcode.modules.organoid_ai import drug_response, simulate_growth, design_organoid


def test_reported_ic50_is_the_half_viability_dose():
    r = drug_response("tumor", list(DRUG_ACTIONS))
    for c, v in r["responses"].items():
        k = DRUG_ACTIONS[c]["kill"]
        viab = 100 / (1 + (v["ic50_uM"] / v["curve_scale_uM"]) ** 1.5 * k)
        assert abs(viab - 50) < 0.05, c


def test_most_effective_uses_potency_and_skips_uncurated():
    r = drug_response("tumor", ["cisplatin", "olaparib", "made_up"])
    assert r["most_effective"] == "olaparib"  # kill .75 > cisplatin .70
    assert r["uncurated_compounds"] == ["made_up"]
    r2 = drug_response("tumor", ["olaparib", "cisplatin"], ["TP53"])  # TP53 resists cisplatin
    assert r2["responses"]["cisplatin"]["ic50_uM"] > r2["responses"]["olaparib"]["ic50_uM"]


def test_unknown_tissue_rejected_consistently():
    with pytest.raises(KeyError):
        simulate_growth("kidney", 2)
    with pytest.raises(KeyError):
        design_organoid("kidney")


def test_markers_are_official_hgnc_symbols():
    # NCBI Gene (human): GLUL = Gene 2752; BCL11B = Gene 64919.  "GS" also
    # resolves to APC (Gene 324) as an alias, so it was ambiguous.
    z = {t: design_organoid(t)["spatial_expression"]["zones"] for t in ("hepatic", "cerebral")}
    assert "GLUL" in z["hepatic"]["perivenous"] and "GS" not in z["hepatic"]["perivenous"]
    assert "BCL11B" in z["cerebral"]["cortical"] and "CTIP2" not in z["cerebral"]["cortical"]
