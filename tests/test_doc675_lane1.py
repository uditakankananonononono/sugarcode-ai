import random
import pytest
from sugarcode.extra_doc.entity_design675 import apply


def test_history_based_independent_oracle():
    rng=random.Random(675)
    for _ in range(100):
        events=[(str(rng.randrange(4)),rng.randrange(6),str(i)) for i in range(30)]
        accepted=[];rejected=[];histories={}
        for i,(name,version,value) in enumerate(events):
            history=histories.get(name,[])
            if version==len(history):histories.setdefault(name,[]).append(value);accepted.append(i)
            else:rejected.append(i)
        got=apply(events)
        assert got['accepted']==accepted and got['rejected']==rejected
        assert got['entities']==[(name,len(values),values[-1]) for name,values in sorted(histories.items())]
        assert got['persisted'] is False and got['claim']=='PARTIAL'

class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass

@pytest.mark.parametrize('events,message',[
 (L(),'events must be an exact list with 0..100 entries'),
 ([T(('x',0,''))],'event must be an id, expected version, value tuple'),
 *[([(x,0,'')],'ID must be a nonblank exact string of 1..80 characters') for x in (S('x'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 *[([('x',x,'')],'version must be an integer in 0..100') for x in (True,I(0),-1,101)],
 *[([('x',0,x)],'value must be an exact string with 0..120 characters') for x in (S('x'),'x'*121,None)],
])
def test_invalid(events,message):
    with pytest.raises(ValueError) as exc:apply(events)
    assert str(exc.value)==message


def test_bounds_immutability_zero_width():
    events=[('x'*80,i,'v'*120) for i in range(100)];before=repr(events)
    assert apply(events)['entities']==[('x'*80,100,'v'*120)]
    assert repr(events)==before
    assert apply([('\u200b',0,'')])['entities']==[('\u200b',1,'')]
    assert apply([])['entities']==[]
    assert apply([('x',100,'')])['rejected']==[0]
