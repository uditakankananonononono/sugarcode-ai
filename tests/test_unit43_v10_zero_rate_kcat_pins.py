"""Unit 43 v10 (PARTIAL): zero total-rate SSA step and kcat == 0 pins. Hand-derived."""
import warnings
import numpy as np
import pytest
from sugarcode.modules import virtual_cell  # noqa: F401
from sugarcode.modules.virtual_cell import core

ZERO = {"A": {"basal": 0.0, "vmax": 0.0}}


def test_ssa_zero_total_rate_is_silent_and_stays_empty():
    # all propensities are 0: no division by zero (no numpy RuntimeWarning), no events, samples all zero
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        r = core.simulate_expression(["A"], [], method="gillespie", points=4, hours=3.0, params=ZERO, seed=9)
    assert r["ssa_events"] == 0
    assert r["time_h"] == [0.0, 1.0, 2.0, 3.0]
    assert r["mrna"]["A"] == [0.0] * 4 and r["protein"]["A"] == [0.0] * 4
    assert r["steady_state_protein"] == {"A": 0.0} and r["protein_noise_cv"] == {"A": 0.0}


def test_ssa_zero_rate_other_seed_and_two_genes():
    z2 = {"A": {"basal": 0.0, "vmax": 0.0}, "B": {"basal": 0.0, "vmax": 0.0}}
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        r = core.simulate_expression(["A", "B"], [], method="gillespie", points=3, hours=2.0, params=z2, seed=123)
    assert r["ssa_events"] == 0 and r["mrna"] == {"A": [0.0] * 3, "B": [0.0] * 3}


@pytest.mark.parametrize("zero", [0, 0.0, np.float64(0.0), np.int64(0)])
def test_kcat_zero_refused(zero):
    m = core.central_carbon_model()
    with pytest.raises(ValueError, match="kcat for 'TCA' must be positive"):
        core.expression_to_bounds(m, {"E": 5.0}, {"TCA": "E"}, {"TCA": zero})


def test_kcat_missing_and_tiny_positive():
    m = core.central_carbon_model()
    with pytest.raises(ValueError, match="kcat for 'TCA' must be positive"):
        core.expression_to_bounds(m, {"E": 5.0}, {"TCA": "E"}, {})
    # smallest positive kcat is accepted: cap = 1e-12 * 5
    b = core.expression_to_bounds(m, {"E": 5.0}, {"TCA": "E"}, {"TCA": 1e-12})
    assert b == {"TCA": (0.0, pytest.approx(5e-12))}


def test_ssa_small_positive_total_rate_fires():
    # total = 0.5 (< 1) must still schedule events
    r = core.simulate_expression(["A"], [], method="gillespie", points=50, hours=400.0, seed=2,
                                 params={"A": {"basal": 0.5, "vmax": 0.0, "translation": 0.0}})
    assert r["ssa_events"] > 10 and max(r["mrna"]["A"]) >= 1.0
