import random
import copy
import pytest
from sugarcode.extra_doc.gender1778 import audit_allocations
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)


def test_independent_category_partition_oracle():
    rng=random.Random(1778);cats=list('abcd')
    for _ in range(100):
        rng.shuffle(cats);rows=[(str(i),rng.choice(cats),rng.randrange(1001)) for i in range(30)];groups={c:[] for c in cats}
        for n,c,u in rows:groups[c].append(u)
        assert audit_allocations(cats,rows)=={'allocations':[(c,len(groups[c]),sum(groups[c])) for c in cats],'claim':'PARTIAL','gender_inferred':False,'fairness_validated':False}

@pytest.mark.parametrize('cats',[None,L(['a','b']),('a','b'),[],['a'],list(map(str,range(21))),['a','a'],*[[x,'b'] for x in BAD]])
def test_categories_invalid(cats):
    with pytest.raises(ValueError) as exc:audit_allocations(cats,[('t','a',0)])
    assert str(exc.value)=='categories must be an exact list of 2..20 unique valid labels'

@pytest.mark.parametrize('rows,message',[
 *[(x,'tasks must be an exact list with 1..100 entries') for x in (None,L([('a','a',0)]),(('a','a',0),),[],[(str(i),'a',0) for i in range(101)])],
 *[([x],'task must be an id category units tuple') for x in (['a','a',0],T(('a','a',0)),('a','a'),('a','a',0,1))],
 *[([(x,'a',0)],'task IDs must be unique valid labels') for x in BAD],
 ([('a','a',0),('a','a',0)],'task IDs must be unique valid labels'),
 *[([('a',x,0)],'category must be a known valid label') for x in (*BAD,'unknown')],
 *[([('a','a',x)],'units must be an integer in 0..1000') for x in (None,True,I(0),1.5,-1,1001)],
])
def test_tasks_invalid(rows,message):
    with pytest.raises(ValueError) as exc:audit_allocations(['a','b'],rows)
    assert str(exc.value)==message


def test_caps_singleton_zero_units_and_output_ownership():
    cats=['x'*80,'\u200b']+list(map(str,range(18)));rows=[(str(i),'x'*80,1000) for i in range(100)];before=copy.deepcopy(rows);out=audit_allocations(cats,rows)
    assert out['allocations'][0]==('x'*80,100,100000)
    out['allocations'].clear();assert rows==before
    assert audit_allocations(['a','b'],[('x'*80,'a',0)])['allocations']==[('a',1,0),('b',0,0)]
