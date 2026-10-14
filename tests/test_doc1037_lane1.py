from fractions import Fraction
import random
import pytest
from sugarcode.extra_doc.smc1037 import update


def test_direct_ratio_ess_independent_oracle():
    rng=random.Random(1037)
    for n in range(1,51):
        a=[rng.randrange(1,101) for _ in range(n)];b=[rng.randrange(101) for _ in range(n)];b[0]=1
        products=[a[i]*b[i] for i in range(n)];total=sum(products);ess=Fraction(total**2,sum(x*x for x in products));got=update(a,b)
        assert got['weights']==[(Fraction(x,total).numerator,Fraction(x,total).denominator) for x in products]
        assert got['ess']==(ess.numerator,ess.denominator)
        assert got['claim']=='PARTIAL' and got['filter_validated'] is False

class L(list):pass
class I(int):pass
@pytest.mark.parametrize('a,b,message',[
 (L([1]),[1],'prior must be an exact list with 1..50 entries'),
 ([],[],'prior must be an exact list with 1..50 entries'),
 ([1],L([1]),'likelihood must be an exact list matching prior count'),
 ([1],[1,1],'likelihood must be an exact list matching prior count'),
 *[([x],[1],'weights must be integers in 0..100') for x in (True,I(1),-1,101)],
 *[([1],[x],'weights must be integers in 0..100') for x in (True,I(1),-1,101)],
 ([0],[100],'updated weight sum must be positive'),
])
def test_invalid(a,b,message):
    with pytest.raises(ValueError) as exc:update(a,b)
    assert str(exc.value)==message


def test_uniform_and_zero_weights():
    assert update([100]*50,[100]*50)['ess']==(50,1)
    assert update([0,1],[100,1])['weights']==[(0,1),(1,1)]
