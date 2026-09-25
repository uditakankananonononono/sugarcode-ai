"""Real-behavior validation for microbiome_rx (module 107).

BUG 78: optimize_intervention's .02/g input penalty was ~1000x larger than
the squared metabolite errors this model produces (~1e-5 at its natural
~1e-2 output scale), so the penalty always won: EVERY target got
fiber=sugar=0 - even the reachable butyrate 0.005 (achieved 0.00201 instead
of ~0.005). The penalty is now a 1e-6/g tie-breaker and the result reports
target_vs_achieved per metabolite so unreachable targets are visible.
"""
import pytest
from sugarcode.modules.microbiome_rx import core as mr

PROF = {"Bacteroides": 0.3, "Escherichia": 0.2, "Lactobacillus": 0.1,
        "Bifidobacterium": 0.1, "Faecalibacterium": 0.1, "Akkermansia": 0.05}


def test_reachable_target_gets_nonzero_diet_and_hits_it():
    o = mr.optimize_intervention(PROF, {"butyrate": 0.005}, days=5)
    assert o["diet"]["fiber"] > 0.5
    assert o["target_vs_achieved"]["butyrate"]["abs_error"] < 0.001


def test_unreachable_target_pushes_best_effort_and_reports_gap():
    o = mr.optimize_intervention(PROF, {"butyrate": 0.5}, days=5)
    assert o["diet"]["fiber"] == pytest.approx(3.0, abs=0.01)
    tva = o["target_vs_achieved"]["butyrate"]
    assert tva["achieved"] < 0.02 and tva["abs_error"] > 0.48  # visible, not silent


def test_optimizer_deterministic():
    a = mr.optimize_intervention(PROF, {"butyrate": 0.005}, days=5)
    b = mr.optimize_intervention(PROF, {"butyrate": 0.005}, days=5)
    assert a["diet"] == b["diet"]


def test_metabolic_sim_metabolites_respond_to_fiber():
    lo = mr.simulate_metabolic_community(PROF, days=5, diet={"fiber": 0.2}, sample_hours=24)
    hi = mr.simulate_metabolic_community(PROF, days=5, diet={"fiber": 2.5}, sample_hours=24)
    assert hi["final_metabolites"]["butyrate"] > lo["final_metabolites"]["butyrate"]
    assert hi["final_metabolites"]["acetate"] > lo["final_metabolites"]["acetate"]


def test_legacy_antibiotic_and_shift_shapes():
    r = mr.simulate_community(PROF, days=7)
    assert set(r["metabolite_flux"]) >= {"butyrate", "acetate", "lactate"}
    assert abs(sum(r["dysbiosis_shift"].values())) < 0.01  # shares sum to ~0
    c = mr.simulate_community(PROF, days=7, antibiotic="ciprofloxacin")
    assert c["final_relative"].get("Escherichia", 0) <= r["final_relative"].get("Escherichia", 0) + 1e-9


def test_diagnostics_exactly_fifty_across_community_sizes():
    for n in (4, 5, 6):
        p = dict(list(PROF.items())[:n])
        r = mr.analyze_microbiome(p, {"butyrate": 0.005}, days=2)
        assert len(r["diagnostics"]) == 50, n
