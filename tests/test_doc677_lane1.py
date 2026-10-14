import random
import pytest
from sugarcode.extra_doc.domain_event677 import replay


def test_independent_accepted_log_oracle():
    rng=random.Random(677)
    for _ in range(100):
        events=[(str(rng.randrange(15)),str(rng.randrange(3)),rng.randrange(1,8),rng.randrange(-10,11)) for _ in range(30)]
        log=[];ok=[];bad=[]
        for i,row in enumerate(events):
            history=[r for r in log if r[1]==row[1]]
            if any(r[0]==row[0] for r in log) or row[2]!=len(history)+1:bad.append(i)
            else:log.append(row);ok.append(i)
        expected=[(e,len([r for r in log if r[1]==e]),sum(r[3] for r in log if r[1]==e)) for e in sorted({r[1] for r in log})]
        got=replay(events);assert got['entities']==expected and got['accepted']==ok and got['rejected']==bad
        assert got['persisted'] is False and got['claim']=='PARTIAL'

class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass

@pytest.mark.parametrize('events,message',[
 (L(),'events must be an exact list with 0..100 entries'),
 ([T(('x','a',1,0))],'event must be an id, entity, sequence, delta tuple'),
 *[([(x,'a',1,0)],'IDs must be nonblank exact strings of 1..80 characters') for x in (S('x'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 *[([('x','a',x,0)],'sequence must be an integer in 1..100') for x in (True,I(1),0,101)],
 *[([('x','a',1,x)],'delta must be an integer in -100..100') for x in (True,I(1),-101,101)],
])
def test_invalid(events,message):
    with pytest.raises(ValueError) as exc:replay(events)
    assert str(exc.value)==message


def test_retry_unconsumed_ids_sequence_and_bounds():
    events=[('x','a',2,100),('x','a',1,-100),('y','a',2,100),('x','b',1,0)]
    assert replay(events)['accepted']==[1,2] and replay(events)['rejected']==[0,3]
    assert replay(events)['entities']==[('a',2,0)]
    assert replay([(str(i),'a',i+1,0) for i in range(100)])['entities']==[('a',100,0)]
    assert replay([('\u200b','x'*80,1,0)])['accepted']==[0]
