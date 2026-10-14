from fractions import Fraction
import itertools
import pytest
from sugarcode.extra_doc.ekf1040 import update


def test_independent_information_form_oracle():
    for x,z,p,r in itertools.product((-3,1,4),(-8,0,7),(1,3,100),(1,4,100)):
        j=2*x;precision=Fraction(1,p)+Fraction(j*j,r);v=1/precision
        gain=v*Fraction(j,r);posterior=x+gain*(z-x*x);got=update(x,p,z,r)
        assert tuple(got[k] for k in ('mean','variance','gain'))==tuple((a.numerator,a.denominator) for a in (posterior,v,gain))
        assert got['claim']=='PARTIAL' and got['linearization_validated'] is False

class I(int):pass
@pytest.mark.parametrize('args,message',[
 *[(tuple(x if i==pos else [0,1,0,1][i] for i in range(4)),'mean and measurement must be integers in -100..100') for pos in (0,2) for x in (True,I(0),-101,101)],
 *[((0,x,0,1),'variance must be an integer in 0..100') for x in (True,I(0),-1,101)],
 *[((0,1,0,x),'noise must be an integer in 1..100') for x in (True,I(1),0,101)],
])
def test_invalid(args,message):
    with pytest.raises(ValueError) as exc:update(*args)
    assert str(exc.value)==message


def test_zero_jacobian_variance_and_endpoints():
    assert update(0,100,100,100)['variance']==(100,1)
    assert update(-100,0,100,100)['mean']==(-100,1)
    assert update(100,100,-100,1)['claim']=='PARTIAL'
