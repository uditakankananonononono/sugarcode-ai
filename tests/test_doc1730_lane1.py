from itertools import groupby
import random
import pytest
from sugarcode.extra_doc.interview1730 import audit


def test_independent_contiguous_group_oracle():
    rng=random.Random(1730)
    for _ in range(100):
        topics=['a','b','c'];rows=[(str(i),rng.choice('abcd'),rng.randrange(1,61)) for i in range(20)]
        groups=[k for k,g in groupby(row[1] for row in rows)];got=audit(topics,rows)
        assert got['uncovered']==[t for t in topics if t not in groups] and got['revisited']==[t for t in topics if groups.count(t)>1]
        assert got['unknown']==[n for n,t,m in rows if t not in topics] and got['minutes']==sum(m for n,t,m in rows)
        assert got['claim']=='PARTIAL' and got['interview_validated'] is False

class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
@pytest.mark.parametrize('topics,rows,message',[
 (L(['a']),[],'topics must be an exact list with 1..20 entries'),
 ([],[],'topics must be an exact list with 1..20 entries'),
 ([str(i) for i in range(21)],[],'topics must be an exact list with 1..20 entries'),
 *[([x],[],'topics must be unique valid labels') for x in (S('a'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 (['a'],L(),'questions must be an exact list with 0..50 entries'),
 (['a'],[(str(i),'a',1) for i in range(51)],'questions must be an exact list with 0..50 entries'),
 (['a'],[T(('a','a',1))],'question must be an id topic minutes tuple'),
 (['a'],[('a','a',1,1)],'question must be an id topic minutes tuple'),
 (['a'],[(S('a'),'a',1)],'question IDs must be unique valid labels'),
 (['a'],[('a',S('a'),1)],'question topic must be a valid label'),
 *[(['a'],[('a','a',x)],'minutes must be an integer in 1..60') for x in (True,I(1),0,61,1.5)],
])
def test_invalid(topics,rows,message):
    with pytest.raises(ValueError) as exc:audit(topics,rows)
    assert str(exc.value)==message


def test_caps_and_unknown_breaks_known_run():
    topics=list(map(str,range(20)));rows=[(str(i),str(i%20),60) for i in range(50)];assert audit(topics,rows)['minutes']==3000
    assert audit(['x'*80],[('\u200b','x'*80,1)])['uncovered']==[]
    assert audit(['a'],[('1','a',1),('2','x',1),('3','a',1)])['revisited']==['a']
