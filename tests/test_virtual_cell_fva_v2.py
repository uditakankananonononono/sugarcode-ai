"""v2 delta for unit 43: negative-optimum convention. Documented convention:
objective >= optimum - (1 - fraction) * |optimum|   (equals fraction*optimum when optimum >= 0).
Toy model: reactions v1 (uptake 0..1000 free), v2 objective, S = [[1, -1]] so v1 = v2,
bounds v2 in [-2, -1]; optimum (max v2) = -1."""
import numpy as np
import pytest
from sugarcode.modules.virtual_cell import MetabolicModel, demo_model
from sugarcode.modules.virtual_cell.fva import flux_variability


def neg_model():
    return MetabolicModel(["M"], ["v1", "v2"], np.array([[1.0, -1.0]]), np.array([-2.0, -2.0]), np.array([-1.0, -1.0]), objective="v2")


def test_negative_optimum_does_not_go_infeasible():
    r = flux_variability(neg_model(), fraction_of_optimum=0.5)
    assert r["status"] == "optimal" and r["optimum"] == pytest.approx(-1.0)
    # bound = -1 - 0.5*1 = -1.5 -> v2 in [-1.5, -1]
    assert r["ranges"]["v2"]["min"] == pytest.approx(-1.5, abs=1e-7)
    assert r["ranges"]["v2"]["max"] == pytest.approx(-1.0, abs=1e-7)
    assert r["objective_bound"] == pytest.approx(-1.5)


@pytest.mark.parametrize("f,lo", [(1.0, -1.0), (0.0, -2.0), (0.25, -1.75)])
def test_negative_convention_formula(f, lo):
    r = flux_variability(neg_model(), fraction_of_optimum=f)
    assert r["ranges"]["v2"]["min"] == pytest.approx(lo, abs=1e-7)


def test_positive_optimum_unchanged():
    r = flux_variability(demo_model(), fraction_of_optimum=0.5)
    assert r["objective_bound"] == pytest.approx(0.5 * r["optimum"], rel=1e-9)
    assert r["ranges"]["GLYCOLYSIS"]["min"] == pytest.approx(5.0, abs=1e-6)


def test_zero_optimum_bound_is_zero():
    m = demo_model()
    r = flux_variability(m, bounds_override={"GLC_UP": (0, 0)}, fraction_of_optimum=0.5)
    assert r["objective_bound"] == pytest.approx(0.0, abs=1e-7)


def test_status_documents_the_convention():
    r = flux_variability(neg_model(), fraction_of_optimum=0.5)
    assert "optimum - (1 - fraction) * |optimum|" in r["status_note"]
