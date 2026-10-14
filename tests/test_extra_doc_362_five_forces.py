from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.five_forces import industry_attractiveness as solve


def test_explicit_five_force_weighted_contribution_oracle():
    r=solve([10,20,30,40,50],[1,2,3,4,5])
    assert r=={'forces':[{'force':name,'pressure':p,'contribution':c} for name,p,c in
                        [('rivalry',10,F(2,3)),('entrants',20,F(8,3)),('substitutes',30,6),
                         ('suppliers',40,F(32,3)),('buyers',50,F(50,3))]],
              'weighted_pressure':F(110,3),'attractiveness':F(190,3),'assessment_validated':False}


def test_endpoints_ignored_zero_weight():
    assert solve([0]*5,[1000]*5)['attractiveness']==100
    assert solve([100]*5,[1000]*5)['attractiveness']==0
    assert solve([0,100,100,100,100],[1,0,0,0,0])['weighted_pressure']==0

@pytest.mark.parametrize('args,error,message',[
 ((None,[1]*5),TypeError,'inputs must be lists or tuples'),
 (([0]*5,None),TypeError,'inputs must be lists or tuples'),
 (([],[1]*5),ValueError,'exactly five pressures and weights required'),
 (([0]*6,[1]*5),ValueError,'exactly five pressures and weights required'),
 (([0]*5,[1]*4),ValueError,'exactly five pressures and weights required'),
 (([0]*5,[1]*6),ValueError,'exactly five pressures and weights required'),
 (([0]*5,[0]*5),ValueError,'at least one weight must be positive'),
])
def test_shapes(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('bad',[True,-1,101,None,1.0])
def test_pressures(bad):
    with pytest.raises(ValueError) as exc:solve([0,0,bad,0,0],[1]*5)
    assert str(exc.value)=='pressures must be nonbool integers zero through 100'

@pytest.mark.parametrize('bad',[True,-1,1001,None,1.0])
def test_weights(bad):
    with pytest.raises(ValueError) as exc:solve([0]*5,[1,1,bad,1,1])
    assert str(exc.value)=='weights must be nonbool integers zero through 1000'
