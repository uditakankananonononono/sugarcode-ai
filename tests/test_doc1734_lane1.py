import random
import pytest
from sugarcode.extra_doc.field1734 import conflicts


def test_independent_disjoint_interval_oracle():
    rng=random.Random(1734)
    for _ in range(100):
        visits=[]
        for i in range(20):
            start=rng.randrange(1440);visits.append((str(i),rng.choice('ab'),start,rng.randrange(start+1,1441)))
        expected=[]
        for i,(a,site,s,e) in enumerate(visits):
            for b,other,x,y in visits[i+1:]:
                if site==other and not(e<=x or y<=s):expected.append((a,b))
        got=conflicts(visits);assert got['overlaps']==expected
        assert got['claim']=='PARTIAL' and got['field_conditions_validated'] is False

class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
@pytest.mark.parametrize('rows,message',[
 (L(),'visits must be an exact list with 0..50 entries'),
 ([(str(i),'a',0,1) for i in range(51)],'visits must be an exact list with 0..50 entries'),
 ([T(('a','b',0,1))],'visit must be an id site start end tuple'),
 ([('a','b',0,1,1)],'visit must be an id site start end tuple'),
 *[([tuple(x if j==pos else ['a','b',0,1][j] for j in range(4))],'labels must be valid with unique visit IDs') for pos in (0,1) for x in (S('a'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 *[([tuple(x if j==pos else ['a','b',0,1][j] for j in range(4))],'times must be integers with 0<=start<end<=1440') for pos in (2,3) for x in (True,I(0),-1,1441,1.5)],
 ([('a','b',1,1)],'times must be integers with 0<=start<end<=1440'),
])
def test_invalid(rows,message):
    with pytest.raises(ValueError) as exc:conflicts(rows)
    assert str(exc.value)==message


def test_caps_touching_site_and_label():
    assert len(conflicts([(str(i),'a',0,1440) for i in range(50)])['overlaps'])==1225
    assert conflicts([('x'*80,'\u200b',0,1),('b','\u200b',1,1440)])['overlaps']==[]
    assert conflicts([('a','x',0,2),('b','y',0,2)])['overlaps']==[]
