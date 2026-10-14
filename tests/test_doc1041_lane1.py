from fractions import Fraction
import itertools
import pytest
from sugarcode.extra_doc.ukf1041 import transform


def test_independent_derived_polynomial_oracle():
    for m,s in itertools.product(range(-10,11),range(1,11)):
        average=Fraction(m*m)+Fraction(s*s,3)
        variance=Fraction(4*m*m*s*s,3)+Fraction(2*s**4,9)
        cross=Fraction(2*m*s*s,3);got=transform(m,s)
        assert tuple(got[k] for k in ('output_mean','output_variance','cross_covariance'))==tuple((v.numerator,v.denominator) for v in (average,variance,cross))
        assert got['claim']=='PARTIAL' and got['approximation_validated'] is False

class I(int):pass
@pytest.mark.parametrize('args,message',[
 *[((x,1),'mean must be an integer in -100..100') for x in (True,I(0),-101,101)],
 *[((0,x),'spread must be an integer in 1..100') for x in (True,I(1),0,101)],
])
def test_invalid(args,message):
    with pytest.raises(ValueError) as exc:transform(*args)
    assert str(exc.value)==message


def test_endpoints_and_zero_cross():
    assert transform(-100,100)['cross_covariance']==(-2000000,3)
    assert transform(100,100)['cross_covariance']==(2000000,3)
    assert transform(0,1)['cross_covariance']==(0,1)
