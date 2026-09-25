"""Module 127 virtual_cell: solver-infeasibility vs biological no-growth,
glucose validation, pFBA fraction honesty, Boolean initial-state validation.
Catalog anchors: PMID 26115539 and PMID 29275251 (whole-cell modeling
principles)."""
import json
import pytest
from sugarcode.modules.virtual_cell import (central_carbon_model, demo_model,
    environment_response, fba, pfba, regulatory_state, simulate_growth,
    virtual_cell_report)


def test_infeasible_condition_is_not_sold_as_no_growth():
    m = central_carbon_model()
    r = environment_response(m, {"broken": {"GLC_UP": (5, 2)}, "starved": {"GLC_UP": (0, 0)}})
    assert r["conditions"]["broken"]["status"] == "infeasible"
    assert "infeasible" in r["conditions"]["broken"]["phenotype"]  # was: "no growth"
    # a genuinely starved but feasible condition still says no growth
    assert r["conditions"]["starved"]["status"] == "optimal"
    assert r["conditions"]["starved"]["phenotype"] == "no growth"


def test_fba_infeasible_keeps_result_shape():
    r = fba(central_carbon_model(), bounds_override={"GLC_UP": (5, 2)})
    assert r["status"] == "infeasible" and r["objective_reaction"] == "BIOMASS"
    assert set(r) == {"status", "objective", "objective_reaction", "fluxes"}


def test_simulate_growth_validates_glucose():
    with pytest.raises(ValueError, match="glucose0"):
        simulate_growth(demo_model(), glucose0=0)  # was: IndexError
    with pytest.raises(ValueError, match="glucose0"):
        simulate_growth(demo_model(), glucose0=-1)
    assert simulate_growth(demo_model(), hours=1)["trajectory"]


def test_pfba_fraction_validated_and_normal_path_intact():
    m = central_carbon_model()
    for bad in (2.0, -1.0, 0.0):
        with pytest.raises(ValueError, match="optimum_fraction"):
            pfba(m, optimum_fraction=bad)  # was: silent plain-FBA fallback for 2.0
    r = pfba(m)
    assert r["method"] == "pFBA" and r["total_flux"] > 0


def test_boolean_initial_state_validated():
    with pytest.raises(ValueError, match="within \[0, 1\]"):
        regulatory_state(["a", "b"], [("a", "b", 1)], initial={"a": 5.0})
    with pytest.raises(ValueError, match="unknown genes"):
        regulatory_state(["a", "b"], [("a", "b", 1)], initial={"ghost": 1})
    r = regulatory_state(["sensor", "resp"], [("sensor", "sensor", 1), ("sensor", "resp", 1)], {"sensor": 1})
    assert r["steady_state"] == {"sensor": 1.0, "resp": 1.0} and r["converged"]


def test_end_to_end_report_and_json_intact():
    r = virtual_cell_report()
    assert r["baseline"]["objective"] > 0 and len(r["environment"]["conditions"]) == 2
    json.dumps(r)


def test_pubmed_whole_cell_anchors_live():
    from sugarcode.bio.entrez import esummary
    try:
        s = esummary("pubmed", ["26115539", "29275251"])
    except Exception as e:
        pytest.skip("entrez unavailable: %s" % e)
    assert "whole-cell" in s["26115539"]["title"].lower()
    assert "whole-cell" in s["29275251"]["title"].lower()
