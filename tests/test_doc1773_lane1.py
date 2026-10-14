import random
import copy
from fractions import Fraction
import pytest
from sugarcode.extra_doc.democratization1773 import compare_scores
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)


def test_independent_minmax_time_join_oracle():
    rng=random.Random(1773);criteria=list('abcd')
    for _ in range(100):
        rows=[(t,[rng.randrange(11) for c in criteria]) for t in rng.sample(range(1001),10)];rng.shuffle(rows);first=min(rows)[1];last=max(rows)[1]
        changes=[(c,a,b,b-a) for c,a,b in zip(criteria,first,last)];means=[]
        for t in sorted(t for t,s in rows):
            s=next(s for u,s in rows if u==t);f=sum((Fraction(x,4) for x in s));means.append((t,(f.numerator,f.denominator)))
        assert compare_scores(criteria,rows)=={'changes':changes,'means':means,'claim':'PARTIAL','democracy_inferred':False}

@pytest.mark.parametrize('criteria',[None,L(['a']),('a',),[],list(map(str,range(21))),['a','a'],*[[x] for x in BAD]])
def test_criteria_invalid(criteria):
    with pytest.raises(ValueError) as exc:compare_scores(criteria,[(0,[0]),(1,[1])])
    assert str(exc.value)=='criteria must be an exact list of 1..20 unique valid labels'

@pytest.mark.parametrize('rows,message',[
 *[(x,'waves must be an exact list with 2..20 entries') for x in (None,L([(0,[0]),(1,[1])]),((0,[0]),(1,[1])),[],[(0,[0])],[(i,[0]) for i in range(21)])],
 *[([x,(1,[1])],'wave must be a time scores tuple') for x in ([0,[0]],T((0,[0])),(0,),(0,[0],1))],
 *[([(x,[0]),(1,[1])],'times must be unique exact integers in 0..1000') for x in (None,True,I(0),1.5,-1,1001)],
 ([(0,[0]),(0,[1])],'times must be unique exact integers in 0..1000'),
 *[([(0,x),(1,[1])],'scores must be an exact list matching criteria with integers in 0..10') for x in (None,L([0]),(0,),[],[0,1],*[ [x] for x in (None,True,I(0),1.5,-1,11)])],
])
def test_waves_invalid(rows,message):
    with pytest.raises(ValueError) as exc:compare_scores(['a'],rows)
    assert str(exc.value)==message


def test_caps_one_criterion_minimum_waves_and_ownership():
    criteria=['x'*80,'\u200b']+list(map(str,range(18)));rows=[(i,[10]*20) for i in range(20)];before=copy.deepcopy(rows);out=compare_scores(criteria,rows);assert out['means']==[(i,(10,1)) for i in range(20)]
    out['changes'].clear();out['means'].clear();assert rows==before
    assert compare_scores(['a'],[(0,[0]),(1000,[10])])['changes']==[('a',0,10,10)]
