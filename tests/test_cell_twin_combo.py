"""Regression tests for BUG 61 (max_apoptosis took last-listed dose) and
BUG 62 (combination screen claimed a mechanistic rerun but just added 0.08)."""
import math
import numpy as np
import pytest
from sugarcode.modules import cell_twin as ct
from sugarcode.modules.cell_twin.core import _drug_effect

OMICS = {"mutations": [{"gene": "KRAS", "driver_score": 0.9}],
         "expression": {"MKI67": 120.0, "PCNA": 80.0, "BAX": 50.0, "BCL2": 40.0, "ERCC1": 30.0},
         "proteomics": {}}


def test_max_apoptosis_dose_order_independent():
    twin = ct.create_twin(OMICS)
    asc = ct.run_drug_trial(twin, ["cisplatin"], [0.1, 1.0, 10.0])["per_drug"]["cisplatin"]["max_apoptosis"]
    desc = ct.run_drug_trial(twin, ["cisplatin"], [10.0, 1.0, 0.1])["per_drug"]["cisplatin"]["max_apoptosis"]
    assert asc == desc  # was: descending list returned the min-dose apoptosis


def test_combination_is_actual_rerun_not_constant_bonus():
    twin = ct.build_mechanistic_twin(OMICS)
    screen = ct.combination_screen(twin, ["cisplatin", "trametinib", "olaparib"], [1.0, 1.0, 1.0])
    excesses = [c["bliss_excess"] for c in screen["combinations"]]
    assert len(set(excesses)) > 1  # was: constant +0.08*(1-res)^2 bonus for every pair


def test_combined_effect_matches_ode_and_bliss_scalar():
    twin = ct.build_mechanistic_twin(OMICS)
    comb = ct.simulate_combined_response(twin, "cisplatin", 1.0, "olaparib", 1.0)
    eff_a = _drug_effect(twin, "cisplatin", 1.0)
    eff_b = _drug_effect(twin, "olaparib", 1.0)
    assert comb["combined_effect"] == pytest.approx(1 - (1 - eff_a) * (1 - eff_b), rel=1e-12)
    # independent RK4 cross-check of the combined ODE
    pa = twin["pathway_activities"]; effect = comb["combined_effect"]
    def rhs(y):
        v, a, p, d = y
        growth = .04 * pa["proliferation"] * v * (1 - v / 2); injury = .08 * effect * v
        repair = .03 * pa["dna_repair"] * d; death = injury * (.5 + pa["apoptosis"]) * (1 - .5 * pa["survival"])
        return np.array([growth - death, death - .02 * a, -.05 * effect * p + .02 * pa["proliferation"] * (1 - p), injury - repair - .02 * d])
    y = np.array(list(twin["initial_state"].values())); h = 0.01
    for _ in range(int(72 / h)):
        k1, k2, k3, k4 = rhs(y), rhs(y + h / 2 * rhs(y)), rhs(y + h / 2 * rhs(y + h / 2 * rhs(y))), rhs(y + h * rhs(y + h / 2 * rhs(y + h / 2 * rhs(y))))
        y = y + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    assert abs(y[0] - comb["terminal_viability"]) < 1e-3


def test_mechanistic_twin_pathways_recompute():
    twin = ct.build_mechanistic_twin(OMICS)
    s = 120 + 80  # MKI67 + PCNA expression
    assert twin["pathway_activities"]["proliferation"] == pytest.approx(s / (s + 100), rel=1e-12)
    s2 = 50.0  # BAX only (CASP3/BAK1 absent)
    assert twin["pathway_activities"]["apoptosis"] == pytest.approx(s2 / (s2 + 100), rel=1e-12)
