"""Real-behavior validation for microaiverse (module 106).

BUG 76: cultivation_plan's predicted_success was unbounded - 0.3 + 0.2 per
supplement + 0.2 for partners reached 1.5 (a 150% "probability") with five
gaps, and duplicate gaps stacked identical supplements to inflate it further
(5x the same gap also gave 1.5). Gaps are now deduped and the score is
capped at 0.95 (no cultivation is a certainty). Existing 1-2 gap scores are
unchanged (0.7, 0.9).

BUG 77: optimize_medium crashed inside linprog with a raw solver error
("Invalid input for linprog: c must be a 1-D array...") for a target with no
requirements. The empty medium at zero cost is now returned directly.
"""
import pytest
from sugarcode.modules.microaiverse import core as ma


def test_predicted_success_never_exceeds_cap():
    all_gaps = ["vitamin_B12", "heme_synthesis", "purine_synthesis",
                "fatty_acid_synthesis", "amino_acid_biosynthesis"]
    r = ma.cultivation_plan("X", "syntroph", all_gaps)
    assert r["predicted_success"] == 0.95
    assert len(r["media_recipe"]["supplements"]) == 5


def test_duplicate_gaps_do_not_inflate_score():
    r = ma.cultivation_plan("X", "syntroph", ["vitamin_B12"] * 5)
    assert r["media_recipe"]["supplements"] == ["cobalamin 1 ug/L"]
    assert r["predicted_success"] == 0.7


def test_small_gap_scores_unchanged():
    assert ma.cultivation_plan("X", "auxotroph", ["vitamin_B12"])["predicted_success"] == 0.7
    r = ma.cultivation_plan("X", "syntroph", ["vitamin_B12", "amino_acid_biosynthesis"])
    assert r["predicted_success"] == 0.9


def test_optimize_medium_empty_requirements():
    r = ma.optimize_medium({"name": "t", "requirements": {}}, {"cobalamin": 3.0})
    assert r["supplements"] == {} and r["total_cost"] == 0.0
    assert r["within_budget"] and r["optimal"] and r["requirements_met"] == {}


def test_optimize_medium_matches_analytic_optimum():
    tm = {"name": "t", "requirements": {"cobalamin": 1.0, "heme": 2.0}, "uptake": {"glucose": 1.0}}
    r = ma.optimize_medium(tm, {"cobalamin": 3.0, "heme": 1.5}, budget=10)
    assert r["supplements"] == {"cobalamin": 1.0, "heme": 2.0}
    assert r["total_cost"] == pytest.approx(1.0 * 3.0 + 2.0 * 1.5)
    assert all(r["requirements_met"].values())


def test_partner_ranking_arithmetic():
    tm = {"name": "t", "requirements": {"cobalamin": 1.0, "heme": 2.0}, "uptake": {"glucose": 1.0}}
    pm = [{"name": "p1", "secretion": {"cobalamin": 0.8, "heme": 3.0}, "uptake": {"glucose": 0.5}}]
    row = ma.rank_coculture_partners(tm, pm)["ranking"][0]
    assert row["coverage_fraction"] == pytest.approx((0.8 + 2.0) / 3.0)
    assert row["competition_fraction"] == pytest.approx(0.5 / 1.0)
    assert row["net_crossfeeding_score"] == pytest.approx((0.8 + 2.0) / 3.0 - 0.4 * 0.5)
    assert row["supplied_metabolites"] == {"cobalamin": 0.8, "heme": 2.0}


def test_coculture_ode_runs_and_grows():
    tm = {"name": "t", "requirements": {"cobalamin": 1.0, "heme": 2.0}, "uptake": {"glucose": 1.0}}
    pm = {"name": "p", "secretion": {"cobalamin": 0.8, "heme": 3.0}, "uptake": {"glucose": 0.5}}
    sim = ma.simulate_coculture(tm, pm, {"cobalamin": 1.0, "heme": 2.0}, hours=72)
    assert sim["solver"]["success"]
    assert sim["target_final_biomass"] > 0.01
    assert "no cultivation success claim" in sim["model_status"]
