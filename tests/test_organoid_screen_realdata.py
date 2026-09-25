"""Module 114 organoid_screen: Bliss identities, hit selection, IC50 recovery on known curves."""
import pytest
from sugarcode.modules.cell_twin.core import DRUG_ACTIONS
from sugarcode.modules.organoid_ai import drug_response
from sugarcode.modules.organoid_screen import screen, dose_response, bliss_synergy


def test_synergy_is_not_a_constant():
    r = screen("tumor", list(DRUG_ACTIONS))
    s = r["synergy"]
    assert len(s) == 10
    assert all(x["synergy_score"] is None for x in s)  # no combo data -> no synergy claim
    for x in s:
        va, vb = x["single_viability"]
        assert abs(x["bliss_expected_viability"] - va * vb) < 1e-3
    assert len({x["bliss_expected_viability"] for x in s}) > 1


def test_hit_never_uncurated():
    assert screen("tumor", ["madeup"])["hit"] is None
    assert screen("tumor", ["madeup", "olaparib"])["hit"] == "olaparib"


def test_dose_response_recovers_known_ic50_within_grid_error():
    for c in DRUG_ACTIONS:
        v = drug_response("tumor", [c])["responses"][c]
        est = dose_response(v["doses_uM"], [x / 100 for x in v["viability_pct"]])["ic50_uM"]
        assert abs(est / v["ic50_uM"] - 1) < 0.03, c  # nearest-dose rule was 21% off


def test_dose_response_edge_cases():
    assert dose_response([.1, 1], [.9, .8])["ic50_uM"] is None
    with pytest.raises(ValueError):
        dose_response([.1, 1, 10], [90, 50, 10])
    assert dose_response([10, .1, 1], [.1, .9, .5])["ic50_uM"] == pytest.approx(1.0)
    assert bliss_synergy(.5, .5, .1)["synergistic"]
