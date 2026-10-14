from fractions import Fraction
import pytest
from sugarcode.extra_doc.mle1030 import estimate


def test_independent_observation_product_oracle():
    grid=[(i,10) for i in range(11)]
    for n in range(1,11):
        for s in range(n+1):
            weights=[]
            for a,b in grid:
                p=Fraction(a,b);weight=Fraction(1)
                for _ in range(s):weight*=p
                for _ in range(n-s):weight*=1-p
                weights.append(weight)
            expected=sorted(range(11),key=lambda i:(-weights[i],i))[0];got=estimate(s,n,grid)
            assert got['index']==expected and got['likelihood']==(weights[expected].numerator,weights[expected].denominator)
            assert got['claim']=='PARTIAL' and got['model_validated'] is False

class I(int):pass
class L(list):pass
class T(tuple):pass
@pytest.mark.parametrize('s,n,g,message',[
 (0,True,[(0,1)],'trials must be an integer in 1..100'),
 (I(0),1,[(0,1)],'successes must be an integer in 0..trials'),
 (0,1,L([(0,1)]),'grid must be an exact list with 1..50 entries'),
 (0,1,[],'grid must be an exact list with 1..50 entries'),
 *[(0,1,[x],'grid entries must be integer fraction tuples with 0<=num<=den<=100 and den>=1') for x in (T((0,1)),(True,1),(I(0),1),(0,0),(-1,1),(2,1),(1,101))],
 (0,1,[(1,2),(2,4)],'grid probabilities must be distinct'),
])
def test_invalid(s,n,g,message):
    with pytest.raises(ValueError) as exc:estimate(s,n,g)
    assert str(exc.value)==message


def test_boundaries_tie_maximum():
    assert estimate(0,100,[(0,1),(1,1)])['probability']==(0,1)
    assert estimate(100,100,[(0,1),(1,1)])['probability']==(1,1)
    assert estimate(1,2,[(1,4),(3,4)])['index']==0
    assert estimate(25,50,[(i,100) for i in range(50)])['index']==49
