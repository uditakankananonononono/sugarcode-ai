import itertools,random
from fractions import Fraction
import pytest
from sugarcode.extra_doc.permutation1024 import test as solve


def test_boolean_labels_independent_oracle():
    rng=random.Random(1024)
    for n in range(2,9):
        v=[rng.randrange(-5,6) for _ in range(n)]
        for split in range(1,n):
            observed=abs(Fraction(sum(v[:split]),split)-Fraction(sum(v[split:]),n-split));stats=[]
            for labels in itertools.product((0,1),repeat=n):
                if sum(labels)!=split:continue
                a=[x for x,l in zip(v,labels) if l];b=[x for x,l in zip(v,labels) if not l]
                stats.append(abs(Fraction(sum(a),len(a))-Fraction(sum(b),len(b))))
            p=Fraction(sum(x>=observed for x in stats),len(stats));got=solve(v,split)
            assert got['p']==(p.numerator,p.denominator) and got['total']==len(stats)
            assert got['claim']=='PARTIAL' and got['assumptions_validated'] is False

class L(list):pass
class I(int):pass
@pytest.mark.parametrize('v,s,message',[
 (L([1,2]),1,'values must be an exact list with 2..12 entries'),
 ([1],1,'values must be an exact list with 2..12 entries'),
 *[([x,1],1,'values must be integers in -100..100') for x in (True,I(1),-101,101)],
 *[([1,2],x,'split must be an integer in 1..len(values)-1') for x in (True,I(1),0,2)],
])
def test_invalid(v,s,message):
    with pytest.raises(ValueError) as exc:solve(v,s)
    assert str(exc.value)==message

def test_ties_bounds_max():
    assert solve([1]*12,6)['p']==(1,1)
    assert solve([-100,100],1)['p']==(1,1)
