import random
import pytest
from sugarcode.extra_doc.narrative1745 import audit_events


def test_independent_time_bucket_and_actor_join_oracle():
    rng=random.Random(1745)
    for _ in range(100):
        events=[(str(i),rng.randrange(10),rng.sample(list('abc'),rng.randrange(4))) for i in range(30)];rng.shuffle(events)
        buckets={t:sorted(n for n,time,a in events if time==t) for t in range(10)}
        chronology=[n for t in range(10) for n in buckets[t]]
        positions={n:i for i,(n,t,a) in enumerate(events)}
        inversions=[(n,m) for n,t,a in events for m,u,b in events if positions[n]<positions[m] and t>u]
        spans=[(a,min(t for n,t,aa in events if a in aa),max(t for n,t,aa in events if a in aa)) for a in 'abc']
        assert audit_events(events)=={'chronology':chronology,'inversions':inversions,'ties':[(t,ns) for t,ns in buckets.items() if len(ns)>1],'actor_spans':spans,'claim':'PARTIAL','narrative_validated':False}

class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)
@pytest.mark.parametrize('events,message',[
 *[(x,'events must be an exact list with 1..100 entries') for x in (None,L([('a',0,[])]),(('a',0,[]),),[],[(str(i),0,[]) for i in range(101)])],
 *[([x],'event must be an id time actors tuple') for x in (['a',0,[]],T(('a',0,[])),('a',0),('a',0,[],1))],
 *[([(x,0,[])],'event IDs must be unique valid labels') for x in BAD],
 ([('a',0,[]),('a',1,[])],'event IDs must be unique valid labels'),
 *[([('a',x,[])],'time must be an integer in 0..100') for x in (None,True,I(0),1.5,-1,101)],
 *[([('a',0,x)],'actors must be an exact list of 0..20 unique valid labels') for x in (None,L(),('a',),['a','a'],list(map(str,range(21))),*[[x] for x in BAD])],
])
def test_invalid(events,message):
    with pytest.raises(ValueError) as exc:audit_events(events)
    assert str(exc.value)==message


def test_caps_ties_not_inversions_and_single():
    actors=['x'*80]+list(map(str,range(19)));got=audit_events([(str(i),100,actors[:]) for i in range(100)])
    assert len(got['chronology'])==100 and got['inversions']==[] and len(got['actor_spans'])==20
    assert audit_events([('x'*80,0,['\u200b'])])['actor_spans']==[('\u200b',0,0)]
