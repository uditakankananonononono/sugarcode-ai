from fractions import Fraction
import itertools
import pytest
from sugarcode.extra_doc.mcmc1032 import propagate


def test_independent_closed_form_oracle():
    for a,b,initial,n in itertools.product((Fraction(1,3),Fraction(3,4)),(Fraction(1,5),Fraction(2,3)),(0,1),range(12)):
        stationary=a/(a+b);mass=stationary+(initial-stationary)*(1-a-b)**n
        got=propagate((a.numerator,a.denominator),(b.numerator,b.denominator),initial,n)
        assert got['state1_mass']==(mass.numerator,mass.denominator)
        assert got['stationary_state1']==(stationary.numerator,stationary.denominator)
        assert got['claim']=='PARTIAL' and got['mixing_validated'] is False

class I(int):pass
class T(tuple):pass
@pytest.mark.parametrize('args,message',[
 *[((x,(1,2),0,1),'probabilities must be exact integer fractions with 1<=num<den<=100') for x in (T((1,2)),(True,2),(I(1),2),(0,2),(2,2),(1,101))],
 *[(((1,2),x,0,1),'probabilities must be exact integer fractions with 1<=num<den<=100') for x in (T((1,2)),(0,2))],
 *[(((1,2),(1,2),x,1),'initial must be an exact integer zero or one') for x in (True,I(0),-1,2)],
 *[(((1,2),(1,2),0,x),'steps must be an integer in 0..100') for x in (True,I(0),-1,101)],
])
def test_invalid(args,message):
    with pytest.raises(ValueError) as exc:propagate(*args)
    assert str(exc.value)==message


def test_step_endpoints():
    assert propagate((1,100),(99,100),1,0)['state1_mass']==(1,1)
    assert propagate((1,100),(99,100),1,100)['state1_mass']==(1,100)
