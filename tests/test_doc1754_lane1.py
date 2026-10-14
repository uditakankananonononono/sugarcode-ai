import random
from fractions import Fraction
import pytest
from sugarcode.extra_doc.feminist1754 import summarize_resources
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass


def test_independent_share_and_extreme_oracle():
    rng=random.Random(1754)
    for _ in range(100):
        groups=[(str(i),rng.randrange(1001)) for i in range(10)];total=sum(u for n,u in groups);ordered=sorted(u for n,u in groups)
        shares=[(n,(Fraction(u,total).numerator,Fraction(u,total).denominator)) for n,u in groups]
        assert summarize_resources(groups)=={'total':total,'shares':shares,'minimum':[n for n,u in groups if u==ordered[0]],'maximum':[n for n,u in groups if u==ordered[-1]],'gap':ordered[-1]-ordered[0],'claim':'PARTIAL','fairness_validated':False}

@pytest.mark.parametrize('groups,message',[
 *[(x,'groups must be an exact list with 2..20 entries') for x in (None,L([('a',0),('b',0)]),(('a',0),('b',0)),[],[('a',0)],[(str(i),0) for i in range(21)])],
 *[([x,('b',0)],'group must be an id units tuple') for x in (['a',0],T(('a',0)),('a',),('a',0,1))],
 *[([(x,0),('b',0)],'group IDs must be unique nonblank exact strings of 1..80 characters') for x in (None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 ([('a',0),('a',1)],'group IDs must be unique nonblank exact strings of 1..80 characters'),
 *[([('a',x),('b',0)],'units must be an integer in 0..1000') for x in (None,True,I(0),1.5,-1,1001)],
])
def test_invalid(groups,message):
    with pytest.raises(ValueError) as exc:summarize_resources(groups)
    assert str(exc.value)==message


def test_caps_zero_total_ties_and_zero_width():
    got=summarize_resources([(str(i),1000) for i in range(20)])
    assert got['total']==20000 and got['shares']==[(str(i),(1,20)) for i in range(20)] and got['gap']==0
    got=summarize_resources([('x'*80,0),('\u200b',0)]);assert got['shares']==[('x'*80,None),('\u200b',None)] and got['minimum']==got['maximum']==['x'*80,'\u200b']
