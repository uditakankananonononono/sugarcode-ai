from fractions import Fraction
import itertools
import pytest
from sugarcode.extra_doc.kalman1039 import update


def test_independent_precision_weighted_oracle():
    for m,z,p,r in itertools.product((-10,0,7),(-8,0,5),(1,3,1000),(1,4,1000)):
        precision=Fraction(1,p)+Fraction(1,r);v=1/precision;posterior=v*(Fraction(m,p)+Fraction(z,r));got=update(m,p,z,r)
        assert got['mean']==(posterior.numerator,posterior.denominator) and got['variance']==(v.numerator,v.denominator)
        assert got['claim']=='PARTIAL' and got['model_validated'] is False

class I(int):pass
@pytest.mark.parametrize('args,message',[
 *[(tuple(x if i==pos else [0,1,0,1][i] for i in range(4)),'mean and measurement must be integers in -1000..1000') for pos in (0,2) for x in (True,I(0),-1001,1001)],
 *[((0,x,0,1),'variance must be an integer in 0..1000') for x in (True,I(0),-1,1001)],
 *[((0,1,0,x),'noise must be an integer in 1..1000') for x in (True,I(1),0,1001)],
])
def test_invalid(args,message):
    with pytest.raises(ValueError) as exc:update(*args)
    assert str(exc.value)==message


def test_zero_variance_endpoints_and_gain():
    assert update(-1000,0,1000,1000)=={'mean':(-1000,1),'variance':(0,1),'gain':(0,1),'claim':'PARTIAL','model_validated':False}
    assert update(0,1,0,1)['gain']==(1,2)
