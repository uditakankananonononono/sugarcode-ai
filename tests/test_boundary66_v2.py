import math
import pytest
from sugarcode.modules.riboswitch.boundary_response import response_curve
from sugarcode.modules.riboswitch.finite_response import response_curve as finite_response


def test_derived_overflow_refused():
    assert math.isinf(response_curve(1,basal=5e-324,maximum=1e100,concentrations=[0,1])['dynamic_range'])
    with pytest.raises(ValueError,match='UNREPRESENTABLE:'):
        finite_response(1,basal=5e-324,maximum=1e100,concentrations=[0,1])


def test_no_finite_case_regression():
    r=finite_response(1,basal=.25,maximum=1,concentrations=[0,1,2])
    assert r['dynamic_range']==4
    assert r['curve'][1]['occupancy']==.5


def test_zero_basal_preserves_explicit_undefined_ratio():
    assert finite_response(1,basal=0,concentrations=[0,1])['dynamic_range'] is None
