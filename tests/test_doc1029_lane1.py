from fractions import Fraction
import random
import pytest
from sugarcode.extra_doc.multiple_imputation1029 import pool


def test_pairwise_difference_independent_oracle():
    rng=random.Random(1029)
    for m in range(2,21):
        estimates=[rng.randrange(-1000,1001) for _ in range(m)];variances=[rng.randrange(1000001) for _ in range(m)]
        mean=Fraction(sum(estimates),m);within=Fraction(sum(variances),m)
        between=Fraction(sum((a-b)**2 for a in estimates for b in estimates),2*m*(m-1))
        total=within+Fraction(m+1,m)*between;got=pool(estimates,variances)
        assert tuple(got[k] for k in ('mean','within','between','total'))==tuple((x.numerator,x.denominator) for x in (mean,within,between,total))
        assert got['claim']=='PARTIAL' and got['imputation_model_validated'] is False

class L(list):pass
class I(int):pass
@pytest.mark.parametrize('e,v,message',[
 (L([0,0]),[0,0],'estimates must be an exact list with 2..20 entries'),
 ([0],[0],'estimates must be an exact list with 2..20 entries'),
 *[([x,0],[0,0],'estimates must be integers in -1000..1000') for x in (True,I(0),-1001,1001)],
 ([0,0],L([0,0]),'variances must be an exact list matching estimate count'),
 ([0,0],[0],'variances must be an exact list matching estimate count'),
 *[([0,0],[x,0],'variances must be integers in 0..1000000') for x in (True,I(0),-1,1000001)],
])
def test_invalid(e,v,message):
    with pytest.raises(ValueError) as exc:pool(e,v)
    assert str(exc.value)==message


def test_constants_exact_half_endpoint():
    assert pool([0,0],[0,0])['total']==(0,1)
    assert pool([-1000,1000],[1000000,1000000])['total']==(4000000,1)
    assert pool([0,1],[0,0])['between']==(1,2)
