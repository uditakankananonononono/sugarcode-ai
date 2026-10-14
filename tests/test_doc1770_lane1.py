import random
import copy
import pytest
from sugarcode.extra_doc.collective1770 import audit_contributions
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass


def test_independent_removal_sum_oracle():
    rng=random.Random(1770)
    for _ in range(100):
        rows=[(str(i),rng.randrange(1001)) for i in range(10)];threshold=rng.randint(1,10000);total=sum(u for n,u in rows)
        pivotal=[n for n,u in rows if sum(v for m,v in rows if m!=n)<threshold<=total]
        assert audit_contributions(rows,threshold)=={'total':total,'shortfall':threshold-total if total<threshold else 0,'met':total>=threshold,'pivotal':pivotal,'claim':'PARTIAL','action_validated':False}

@pytest.mark.parametrize('rows,message',[
 *[(x,'participants must be an exact list with 1..100 entries') for x in (None,L([('a',0)]),(('a',0),),[],[(str(i),0) for i in range(101)])],
 *[([x],'participant must be an id units tuple') for x in (['a',0],T(('a',0)),('a',),('a',0,1))],
 *[([(x,0)],'participant IDs must be unique nonblank exact strings of 1..80 characters') for x in (None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 ([('a',0),('a',1)],'participant IDs must be unique nonblank exact strings of 1..80 characters'),
 *[([('a',x)],'units must be an integer in 0..1000') for x in (None,True,I(0),1.5,-1,1001)],
])
def test_participants_invalid(rows,message):
    with pytest.raises(ValueError) as exc:audit_contributions(rows,1)
    assert str(exc.value)==message

@pytest.mark.parametrize('threshold',(None,True,I(1),1.5,0,10001))
def test_threshold_invalid(threshold):
    with pytest.raises(ValueError) as exc:audit_contributions([('a',0)],threshold)
    assert str(exc.value)=='threshold must be an integer in 1..10000'


def test_caps_single_zero_exact_threshold_and_ownership():
    assert audit_contributions([(str(i),1000) for i in range(100)],10000)['total']==100000
    assert audit_contributions([('x'*80,0)],1)['shortfall']==1
    rows=[('\u200b',1000)];out=audit_contributions(rows,1000);assert out['pivotal']==['\u200b'];out['pivotal'].clear();assert rows==[('\u200b',1000)]
    assert audit_contributions([('a',1),('b',1)],1)['pivotal']==[]
