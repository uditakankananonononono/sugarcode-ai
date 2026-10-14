from fractions import Fraction
import itertools
import pytest
from sugarcode.extra_doc.metropolis1035 import decide


def test_independent_capped_ratio_crossmultiply_oracle():
    for old,new,fwd,rev,u in itertools.product((1,2,5),(1,3),(1,4),(1,2),(Fraction(0),Fraction(1,2),Fraction(3,4))):
        numerator,denominator=new*rev,old*fwd
        p=Fraction(numerator,denominator) if numerator<denominator else Fraction(1)
        got=decide(old,new,fwd,rev,(u.numerator,u.denominator))
        accepted=u.numerator*denominator<u.denominator*numerator
        assert got['probability']==(p.numerator,p.denominator) and got['accepted']==accepted
        assert got['claim']=='PARTIAL' and got['stationarity_validated'] is False

class I(int):pass
class T(tuple):pass
@pytest.mark.parametrize('args,message',[
 *[(tuple(x if i==pos else 1 for i in range(4))+((0,1),),'weights must be exact integers in 1..100') for pos in range(4) for x in (True,I(1),0,101)],
 *[((1,1,1,1,x),'draw must be an exact integer fraction with 0<=num<den<=100') for x in (T((0,1)),(True,2),(I(0),2),(-1,2),(2,2),(0,101))],
])
def test_invalid(args,message):
    with pytest.raises(ValueError) as exc:decide(*args)
    assert str(exc.value)==message


def test_exact_tie_and_capping():
    assert decide(2,1,1,1,(1,2))['accepted'] is False
    assert decide(1,100,1,100,(99,100))['probability']==(1,1)
