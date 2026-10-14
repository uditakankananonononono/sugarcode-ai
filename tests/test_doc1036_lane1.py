from fractions import Fraction
import itertools
import pytest
from sugarcode.extra_doc.hmc1036 import integrate


def test_independent_linear_map_oracle():
    for q,p,h,n in itertools.product((-2,0,3),(-1,0,4),(Fraction(1,4),Fraction(1)),range(1,8)):
        x,y=Fraction(q),Fraction(p)
        # Derived closed one-step linear map, distinct from half-step implementation.
        for _ in range(n):x,y=(1-h*h/2)*x+h*y,(-h+h**3/4)*x+(1-h*h/2)*y
        delta=(x*x+y*y-q*q-p*p)/2;got=integrate(q,p,(h.numerator,h.denominator),n)
        assert tuple(got[k] for k in ('position','momentum','energy_delta'))==tuple((v.numerator,v.denominator) for v in (x,y,delta))
        assert got['claim']=='PARTIAL' and got['sampling_validated'] is False

class I(int):pass
class T(tuple):pass
@pytest.mark.parametrize('args,message',[
 *[((x,0,(1,2),1),'coordinates must be exact integers in -100..100') for x in (True,I(0),-101,101)],
 *[((0,0,x,1),'step must be an exact integer fraction with 1<=num<=den<=100') for x in (T((1,2)),(True,2),(I(1),2),(0,2),(3,2),(1,101))],
 *[((0,0,(1,2),x),'steps must be an integer in 1..20') for x in (True,I(1),0,21)],
])
def test_invalid(args,message):
    with pytest.raises(ValueError) as exc:integrate(*args)
    assert str(exc.value)==message


def test_zero_and_endpoints():
    assert integrate(-100,100,(1,100),20)['claim']=='PARTIAL'
    assert integrate(0,0,(1,1),1)['energy_delta']==(0,1)
