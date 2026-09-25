"""Regression (BUG 50): adsorption_kinetics must depend on time (first-order kinetics)."""
import math
from sugarcode.modules.phage_designer import adsorption_kinetics


def test_bound_grows_with_time():
    b1 = adsorption_kinetics(1e6, 100, 1e-3, time_min=10)["bound"]
    b2 = adsorption_kinetics(1e6, 100, 1e-3, time_min=60)["bound"]
    assert b2 > b1 > 0


def test_zero_time_zero_bound():
    assert adsorption_kinetics(1e6, 100, 1e-3, time_min=0)["bound"] == 0.0


def test_first_order_formula():
    r = adsorption_kinetics(1000, 50, 0.01, time_min=20)
    assert abs(r["adsorbed_fraction"] - (1 - math.exp(-0.01 * 50 * 20))) < 1e-12
