from fractions import Fraction
import random
import pytest
from sugarcode.extra_doc.longitudinal1738 import summarize


def test_independent_extreme_time_join_oracle():
    rng=random.Random(1738)
    for _ in range(100):
        rows=[(str(i),t,rng.randrange(1001)) for i in range(8) for t in rng.sample(range(101),5)];rng.shuffle(rows);expected=[]
        for n in sorted({n for n,t,s in rows}):
            points=[(t,s) for name,t,s in rows if name==n];first=min(points);last=max(points);d=last[1]-first[1];p=Fraction(d,last[0]-first[0]);expected.append((n,first,last,d,(p.numerator,p.denominator)))
        got=summarize(rows);assert got['changes']==expected and got['claim']=='PARTIAL' and got['trajectory_validated'] is False

class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
@pytest.mark.parametrize('rows,message',[
 (L([('a',0,0)]),'rows must be an exact list with 1..100 entries'),
 ([], 'rows must be an exact list with 1..100 entries'),
 ([(str(i),0,0) for i in range(101)],'rows must be an exact list with 1..100 entries'),
 ([T(('a',0,0))],'row must be an id time score tuple'),
 ([('a',0,0,1)],'row must be an id time score tuple'),
 *[([(x,0,0)],'IDs must be nonblank exact strings of 1..80 characters') for x in (S('a'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 *[([('a',x,0)],'time must be an integer in 0..100') for x in (True,I(0),-1,101,1.5)],
 *[([('a',0,x)],'score must be an integer in 0..1000') for x in (True,I(0),-1,1001,1.5)],
 ([('a',0,0),('a',0,1)],'ID time pairs must be unique'),
])
def test_invalid(rows,message):
    with pytest.raises(ValueError) as exc:summarize(rows)
    assert str(exc.value)==message


def test_caps_single_point_endpoints():
    assert len(summarize([(str(i),100,1000) for i in range(100)])['changes'])==100
    assert summarize([('x'*80,0,0),('x'*80,100,1000)])['changes'][0][-1]==(10,1)
    assert summarize([('\u200b',0,0)])['changes'][0][-1] is None

@pytest.mark.parametrize('rows,message',[
 ((('a',0,0),),'rows must be an exact list with 1..100 entries'),
 ([['a',0,0]],'row must be an id time score tuple'),
 ([('a',0)],'row must be an id time score tuple'),
 ([(None,0,0)],'IDs must be nonblank exact strings of 1..80 characters'),
 ([('',0,0)],'IDs must be nonblank exact strings of 1..80 characters'),
])
def test_extra_shapes(rows,message):
    with pytest.raises(ValueError) as exc:summarize(rows)
    assert str(exc.value)==message
