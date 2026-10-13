import pytest
from sugarcode.modules.riboswitch.boundary_response import response_curve

def test_ordered_basal_maximum_guard():
    with pytest.raises(ValueError,match='0<=basal<maximum'):response_curve(1,basal=2,maximum=1,concentrations=[0,1])

def test_unknown_mode_guard():
    with pytest.raises(ValueError,match='mode must be on/off'):response_curve(1,mode='bad',concentrations=[0,1])
