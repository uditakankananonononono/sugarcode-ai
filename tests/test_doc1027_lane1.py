from fractions import Fraction
import random,statistics
import pytest
from sugarcode.extra_doc.outlier1027 import detect


def test_independent_halves_median_oracle():
    rng=random.Random(1027)
    for n in range(4,101):
        vals=[rng.randrange(-1000,1001) for _ in range(n)];sorted_v=sorted(vals)
        lower=[Fraction(x) for i,x in enumerate(sorted_v) if i<n//2]
        upper=[Fraction(x) for i,x in enumerate(sorted_v) if i>=(n+1)//2]
        a,b=statistics.median(lower),statistics.median(upper)
        low,high=a-Fraction(3,2)*(b-a),b+Fraction(3,2)*(b-a);got=detect(vals)
        assert tuple(got[k] for k in ('q1','q3','low','high'))==tuple((x.numerator,x.denominator) for x in (a,b,low,high))
        assert got['outliers']==[i for i,x in enumerate(vals) if not low<=x<=high]
        assert got['claim']=='PARTIAL' and got['anomalies_validated'] is False

class L(list):pass
class I(int):pass
@pytest.mark.parametrize('bad,message',[
 (L([0]*4),'values must be an exact list with 4..100 entries'),
 ([0]*3,'values must be an exact list with 4..100 entries'),
 ([0]*101,'values must be an exact list with 4..100 entries'),
 *[([x,0,0,0],'values must be integers in -1000..1000') for x in (True,I(0),-1001,1001,None)],
])
def test_invalid(bad,message):
    with pytest.raises(ValueError) as exc:detect(bad)
    assert str(exc.value)==message


def test_equal_fences_not_outliers_and_original_order():
    assert detect([0]*100)['outliers']==[]
    # Quartiles0/2 yield fences-3/5, equality not flagged.
    vals=[5,0,0,0,2,2,2,-3];before=list(vals)
    assert detect(vals)['outliers']==[] and vals==before
    assert detect([1000,0,0,0,0,0,0,-1000])['outliers']==[0,7]
