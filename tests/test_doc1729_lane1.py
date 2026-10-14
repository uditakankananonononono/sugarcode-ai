from fractions import Fraction
import random
import pytest
from sugarcode.extra_doc.mode1729 import compare


def test_independent_mean_difference_oracle():
    rng=random.Random(1729)
    for _ in range(100):
        rows=[(str(i),rng.randrange(101),rng.randrange(101)) for i in range(20)];got=compare(rows)
        expected=Fraction(sum(b for n,a,b in rows),len(rows))-Fraction(sum(a for n,a,b in rows),len(rows))
        assert got['mean_difference']==(expected.numerator,expected.denominator) and got['differences']==[(n,b-a) for n,a,b in rows]
        assert got['positive']==sum(a<b for n,a,b in rows) and got['negative']==sum(a>b for n,a,b in rows) and got['equal']==sum(a==b for n,a,b in rows)
        assert got['claim']=='PARTIAL' and got['causal_effect_validated'] is False

class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
@pytest.mark.parametrize('rows,message',[
 (L([('a',0,0)]),'rows must be an exact list with 1..50 entries'),
 ([], 'rows must be an exact list with 1..50 entries'),
 ([(str(i),0,0) for i in range(51)],'rows must be an exact list with 1..50 entries'),
 ([T(('a',0,0))],'row must be an id mode-a mode-b tuple'),
 ([('a',0,0,0)],'row must be an id mode-a mode-b tuple'),
 *[([(x,0,0)],'IDs must be unique nonblank exact strings of 1..80 characters') for x in (S('a'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 *[([tuple('a' if j==0 else x if j==pos else 0 for j in range(3))],'scores must be exact integers in 0..100') for pos in (1,2) for x in (True,I(0),-1,101,1.5)],
])
def test_invalid(rows,message):
    with pytest.raises(ValueError) as exc:compare(rows)
    assert str(exc.value)==message


def test_caps_zero_and_direction():
    assert compare([(str(i),0,100) for i in range(50)])['mean_difference']==(100,1)
    assert compare([('x'*80,100,0)])['mean_difference']==(-100,1)
    assert compare([('\u200b',0,0)])['equal']==1
