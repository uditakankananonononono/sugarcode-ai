"""Real-behavior validation for living_tx (module 104).

Findings from sweep 104:
- The community ODE is a single-inoculum challenge: engineered growth
  vanishes at the shared carrying capacity (total -> 10) while the washout
  loss 0.08*(1-engraftment) persists, so E=0 is the only stable equilibrium
  (per-capita rates -0.008..-0.056/h at the resident equilibrium). Every
  chassis washes out by day 56 at every dose - consistent with clinical
  reality that Nissle-class chassis need repeated dosing (PMID 30102294).
- The verdict was window-blind: days=1 read "persists" (ready_for_lab) only
  because decay had not acted; days=14 reads washed_out for the same design.
  simulation_verdict now carries assessment_window_days,
  washout_timescale_days, and a caution when window < 3 timescales.
- model_status now states the single-inoculum semantics explicitly (the
  legacy _delivery() text prescribes daily x 8 weeks, which the challenge
  deliberately does not model).
External anchors: PMID 10958782 (IL-10 L. lactis colitis) matches
payload_fit IL-10->Lactobacillus 1.0; PMID 30102294 (SYNB1618 Nissle PKU)
matches phenylalanine_degradase->E_coli_Nissle 1.0; PMID 25626737 (GLP-1
Lactobacillus gasseri) contradicts payload_fit GLP-1->Lactobacillus 0.65 -
documented calibration gap, not refitted.
"""
import math
import pytest
from sugarcode.modules.living_tx import core as lt


def test_structural_extinction_all_chassis_56d():
    for ch in lt.CHASSIS:
        sim = lt.simulate_gut_community(ch, "IL-10", dose_cfu=1e9, days=56)
        assert lt.simulation_verdict(sim)["status"] == "washed_out", ch


def test_equilibrium_per_capita_rates_negative():
    s_star = 0.02 / (0.5 + 0.02)  # substrate at the resident-only equilibrium
    for ch, c in lt.CHASSIS.items():
        rate = 0.5 * c["engraftment"] * s_star * (1 - 10 / 10) - 0.08 * (1 - c["engraftment"])
        assert rate < 0, ch


def test_verdict_window_caution_short_not_long():
    v1 = lt.simulation_verdict(lt.simulate_gut_community("Lactobacillus", "IL-10", dose_cfu=1e9, days=1))
    assert v1["status"] == "persists" and "caution" in v1
    assert v1["assessment_window_days"] == 1.0
    v56 = lt.simulation_verdict(lt.simulate_gut_community("Lactobacillus", "IL-10", dose_cfu=1e9, days=56))
    assert v56["status"] == "washed_out" and "caution" not in v56


def test_washout_timescale_matches_ode_loss_rate():
    v = lt.simulation_verdict(lt.simulate_gut_community("Lactobacillus", "IL-10", dose_cfu=1e9, days=2))
    assert v["washout_timescale_days"] == round(1.0 / (0.08 * 0.3) / 24, 2)


def test_model_status_declares_single_inoculum():
    sim = lt.simulate_gut_community("E_coli_Nissle", "GLP-1", days=1)
    assert "single-inoculum" in sim["model_status"]
    assert "no clinical success prediction" in sim["model_status"]


def test_rank_designs_score_math_spot_check():
    r = lt.rank_designs("IL-10", dose_cfu=1e9)
    row = next(x for x in r["ranking"] if x["chassis"] == "E_coli_Nissle")
    dose_scale = (math.log10(1e9) - 5) / 7
    low = 1 - dose_scale
    sw, ew, gw, dw = .18 + .42 * .15, .12 + .38 * low, .12 + .3 * dose_scale, .12 + .18 * dose_scale
    norm = sw + ew + gw + dw + .22
    expect = (sw * .9 + ew * .4 + gw * .95 + dw * (1 - .12) + .22 * .9) / norm
    assert row["score"] == pytest.approx(expect, abs=1e-8)


def test_containment_combined_risk_is_probability_union():
    sim = lt.simulate_gut_community("E_coli_Nissle", "GLP-1", days=1)
    r = lt.containment_risk("E_coli_Nissle", "GLP-1", sim)
    parts = [r["payload_risk"], r["persistence_risk"], r["horizontal_transfer_risk"], r["shedding_risk"]]
    assert r["combined_risk"] == pytest.approx(1 - math.prod(1 - x for x in parts), rel=1e-12)
    assert 0 < r["combined_risk"] < 1


def test_diagnostics_count_and_unique_keys():
    r = lt.design_living_therapy("IL-10", days=2)
    assert len(r["diagnostics"]) == 50 and len(set(r["diagnostics"])) == 50
