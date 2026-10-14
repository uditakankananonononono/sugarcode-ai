"""Unit 43 v8b: tests-only pin for fva L41 (lb/ub finiteness guard), PARTIAL.

Each non-finite or wrong-shape lb/ub must raise ValueError with the exact message before any LP runs
(linprog is stubbed to fail if reached). One positive case shows finite bounds reach the LP.
"""
import types

import pytest

from sugarcode.modules.virtual_cell import fva

MSG = "lb/ub must be finite vectors, one per reaction"


def _model(lb, ub):
    return types.SimpleNamespace(S=[[0.0]], lb=lb, ub=ub, reactions=["r"], metabolites=["m"], objective="r")


@pytest.fixture(autouse=True)
def _no_lp(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("linprog reached")
    monkeypatch.setattr(fva, "linprog", boom)


@pytest.mark.parametrize("lb,ub", [
    ([0.0], [float("inf")]), ([0.0], [float("-inf")]), ([0.0], [float("nan")]),
    ([float("inf")], [1.0]), ([float("-inf")], [1.0]), ([float("nan")], [1.0]),
    ([0.0, 0.0], [1.0]), ([0.0], [1.0, 1.0]),
])
def test_bad_bounds_refused(lb, ub):
    with pytest.raises(ValueError) as e:
        fva.flux_variability(_model(lb, ub))
    assert str(e.value) == MSG


def test_finite_bounds_reach_lp():
    with pytest.raises(AssertionError, match="linprog reached"):
        fva.flux_variability(_model([0.0], [1.0]))
