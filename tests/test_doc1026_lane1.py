from fractions import Fraction
import itertools,statistics
import pytest
from sugarcode.extra_doc.robust1026 import summarize


def test_standard_median_independent_oracle():
    for n in range(1,7):
        for row in itertools.product((-2,0,3),repeat=n):
            vals=list(row);m=statistics.median([Fraction(x) for x in vals])
            d=statistics.median([abs(Fraction(x)-m) for x in vals]);got=summarize(vals)
            assert got['median']==(m.numerator,m.denominator) and got['mad']==(d.numerator,d.denominator)
            assert got['claim']=='PARTIAL' and got['distribution_validated'] is False

class L(list):pass
class I(int):pass
@pytest.mark.parametrize('bad,message',[
 (L([0]),'values must be an exact list with 1..100 entries'),
 ([], 'values must be an exact list with 1..100 entries'),
 ([0]*101,'values must be an exact list with 1..100 entries'),
 *[([x],'values must be integers in -1000..1000') for x in (True,I(0),-1001,1001,None)],
])
def test_invalid(bad,message):
    with pytest.raises(ValueError) as exc:summarize(bad)
    assert str(exc.value)==message


def test_caps_half_values_and_immutability():
    v=[-1000]*50+[1000]*50;before=list(v)
    assert summarize(v)['median']==(0,1) and summarize(v)['mad']==(1000,1)
    assert v==before
    assert summarize([0,1])['mad']==(1,2)
