from fractions import Fraction
import itertools
import pytest
from sugarcode.extra_doc.em1031 import step


def test_odds_ratio_independent_oracle():
    for observations in itertools.product((0,1),repeat=5):
        for w,a,b in ((Fraction(1,2),Fraction(1,4),Fraction(3,4)),(Fraction(1,3),Fraction(2,3),Fraction(1,5))):
            r=[]
            for x in observations:
                odds=w/(1-w)*(a/b if x else (1-a)/(1-b));r.append(odds/(1+odds))
            expected=(sum(r)/5,sum(r[i] for i,x in enumerate(observations) if x)/sum(r),sum(1-r[i] for i,x in enumerate(observations) if x)/(5-sum(r)))
            got=step(list(observations),(w.numerator,w.denominator),(a.numerator,a.denominator),(b.numerator,b.denominator))
            assert tuple(got[k] for k in ('weight','p1','p2'))==tuple((v.numerator,v.denominator) for v in expected)
            assert got['responsibilities']==[(v.numerator,v.denominator) for v in r]
            assert got['claim']=='PARTIAL' and got['convergence_validated'] is False

class L(list):pass
class T(tuple):pass
class I(int):pass
@pytest.mark.parametrize('obs,params,message',[
 (L([0]),((1,2),)*3,'observations must be an exact list with 1..50 entries'),
 ([],((1,2),)*3,'observations must be an exact list with 1..50 entries'),
 *[([x],((1,2),)*3,'observations must be exact integers zero or one') for x in (True,I(0),-1,2)],
 *[([0],tuple(x if i==pos else (1,2) for i in range(3)),'parameters must be exact integer fraction tuples with 1<=num<den<=100') for pos in range(3) for x in (T((1,2)),(True,2),(I(1),2),(0,2),(2,2),(1,101))],
])
def test_invalid(obs,params,message):
    with pytest.raises(ValueError) as exc:step(obs,*params)
    assert str(exc.value)==message


def test_all_zero_one_maximum():
    assert step([0]*50,(1,100),(1,100),(99,100))['p1']==(0,1)
    assert step([1]*50,(99,100),(1,100),(99,100))['p2']==(1,1)
