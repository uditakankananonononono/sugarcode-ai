"""Module 126 tissue_eng: model-consistent vascular-spacing recommendation,
falsy-or input validation, fidelity clamp, and size_mm validation. Catalog
anchors: PMID 40600176 (perfusable bioprinted skin-on-chip for drug testing)
and PMID 38282554 (oxygen-generating printable scaffold for thick tissues)."""
import json
import pytest
from sugarcode.modules.tissue_eng import (design_tissue, calibrate_printing,
    oxygen_profile, viability_forecast, drug_testing_plan)


def test_recommended_spacing_is_not_hypoxic_in_own_model():
    r = oxygen_profile("liver")
    rec = r["recommended_max_spacing_um"]
    assert rec < 400  # was: 400 um, whose midpoint computes to 0% oxygen
    at = oxygen_profile("liver", channel_spacing_um=rec)
    assert at["minimum_oxygen_percent"] >= 5 and at["hypoxic"] is False


def test_zero_channel_spacing_rejected_not_silently_replaced():
    with pytest.raises(ValueError, match="positive"):
        oxygen_profile("skin", channel_spacing_um=0)  # was: silently replaced with 500


def test_fidelity_never_negative():
    r = calibrate_printing("skin", nozzle_um=10000)
    assert r["predicted_fidelity"] == 0.0  # was: -1.12
    assert 0 <= calibrate_printing("skin", nozzle_um=100000)["predicted_fidelity"]


def test_size_mm_validated_everywhere():
    for bad in [(10, 10), (10, 10, -5), (10, 10, 0)]:
        with pytest.raises(ValueError, match="three positive dimensions"):
            design_tissue("skin", bad)
    with pytest.raises(ValueError, match="three positive dimensions"):
        oxygen_profile("skin", size_mm=(10, 10))  # was: IndexError


def test_spec_cases_still_hold():
    r = design_tissue("cardiac_patch", (10, 10, 3))
    assert r["print_parameters"]["n_layers"] == 15 and r["vascularization"]["required"]
    assert viability_forecast("liver", perfused=True)["endpoint_viability"] > \
           viability_forecast("liver", perfused=False)["endpoint_viability"]
    json.dumps(r); json.dumps(drug_testing_plan("skin", ["a"], 2))


def test_pubmed_bioprinting_anchors_live():
    from sugarcode.bio.entrez import esummary
    try:
        s = esummary("pubmed", ["40600176", "38282554"])
    except Exception as e:
        pytest.skip("entrez unavailable: %s" % e)
    assert "skin-on-chip" in s["40600176"]["title"].lower()
    assert "oxygen-generating" in s["38282554"]["title"].lower()
