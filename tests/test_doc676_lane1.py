from dataclasses import FrozenInstanceError
from fractions import Fraction
import pytest
from sugarcode.extra_doc.value_object676 import FractionValue,make


def test_standard_library_oracle_full_grid():
    for n in range(-20,21):
        for d in range(-20,21):
            if not d:continue
            expected=Fraction(n,d);got=make(n,d)
            assert (got.numerator,got.denominator)==(expected.numerator,expected.denominator)
            assert got==make(n*2,d*2) and hash(got)==hash(make(n*2,d*2))


def test_immutable_zero_and_endpoints():
    got=make(2,4)
    with pytest.raises(FrozenInstanceError):got.numerator=99
    assert make(0,-1000000)==FractionValue(0,1)
    assert make(-1000000,1).numerator==-1000000
    assert make(1,1000000).denominator==1000000

class I(int):pass

@pytest.mark.parametrize('call,message',[
 *[(lambda x=x:make(x,1),'inputs must be exact integers') for x in (True,I(1),None)],
 *[(lambda x=x:make(1,x),'inputs must be exact integers') for x in (True,I(1),None)],
 *[(lambda n=n,d=d:make(n,d),'inputs exceed bounds or denominator is zero') for n,d in ((0,0),(1000001,1),(-1000001,1),(1,1000001),(1,-1000001))],
 (lambda:FractionValue(I(1),1),'fields must be exact integers'),
 (lambda:FractionValue(1,True),'fields must be exact integers'),
 (lambda:FractionValue(1,0),'normalized fields exceed bounds'),
 (lambda:FractionValue(1000001,1),'normalized fields exceed bounds'),
 (lambda:FractionValue(2,4),'fields must be normalized coprime integers'),
])
def test_invalid(call,message):
    with pytest.raises(ValueError) as exc:call()
    assert str(exc.value)==message
