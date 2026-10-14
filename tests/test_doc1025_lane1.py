from fractions import Fraction
import random
import pytest
from sugarcode.extra_doc.nonparametric1025 import statistic


def test_pooled_average_rank_independent_oracle():
    rng=random.Random(1025)
    for _ in range(150):
        left=[rng.randrange(6) for _ in range(rng.randrange(1,10))];right=[rng.randrange(6) for _ in range(rng.randrange(1,10))]
        pooled=sorted(left+right);rank_sum=0
        for x in left:
            ranks=[i+1 for i,y in enumerate(pooled) if y==x];rank_sum+=Fraction(sum(ranks),len(ranks))
        u=rank_sum-Fraction(len(left)*(len(left)+1),2);got=statistic(left,right)
        assert got['u']==(u.numerator,u.denominator) and got['pairs']==len(left)*len(right)
        assert got['claim']=='PARTIAL' and got['assumptions_validated'] is False

class L(list):pass
class I(int):pass
@pytest.mark.parametrize('bad,message',[
 (L([1]),'samples must be exact lists with 1..30 entries'),
 ([], 'samples must be exact lists with 1..30 entries'),
 ([1]*31,'samples must be exact lists with 1..30 entries'),
 *[([x],'sample values must be integers in -1000..1000') for x in (True,I(1),-1001,1001)],
])
def test_invalid(bad,message):
    for a,b in ((bad,[1]),([1],bad)):
        with pytest.raises(ValueError) as exc:statistic(a,b)
        assert str(exc.value)==message

def test_ties_max_and_endpoints():
    assert statistic([1],[1])['u']==(1,2)
    assert statistic([-1000]*30,[1000]*30)['u']==(0,1)
    assert statistic([1000]*30,[-1000]*30)['u']==(900,1)
