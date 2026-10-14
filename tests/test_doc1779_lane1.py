import random
import bisect
import pytest
from sugarcode.extra_doc.class1779 import assign_bands
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass


def test_independent_bisect_histogram_oracle():
    rng=random.Random(1779)
    for _ in range(100):
        ts=sorted(rng.sample(range(1,1001),10));rows=[(str(i),rng.randrange(1001)) for i in range(30)];bands=[(n,bisect.bisect_right(ts,u)) for n,u in rows];hist={i:0 for i in range(11)}
        for n,b in bands:hist[b]+=1
        assert assign_bands(ts,rows)=={'bands':bands,'counts':list(hist.items()),'claim':'PARTIAL','class_inferred':False}

@pytest.mark.parametrize('ts',[
 None,L([1]),(1,),[],list(range(1,22)),[1,1],[2,1],
 *[[x] for x in (None,True,I(1),1.5,0,1001)],
])
def test_thresholds_invalid(ts):
    with pytest.raises(ValueError) as exc:assign_bands(ts,[('a',0)])
    assert str(exc.value)=='thresholds must be an exact list of 1..20 strictly increasing integers in 1..1000'

@pytest.mark.parametrize('rows,message',[
 *[(x,'records must be an exact list with 1..100 entries') for x in (None,L([('a',0)]),(('a',0),),[],[(str(i),0) for i in range(101)])],
 *[([x],'record must be an id income tuple') for x in (['a',0],T(('a',0)),('a',),('a',0,1))],
 *[([(x,0)],'record IDs must be unique nonblank exact strings of 1..80 characters') for x in (None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 ([('a',0),('a',1)],'record IDs must be unique nonblank exact strings of 1..80 characters'),
 *[([('a',x)],'income must be an integer in 0..1000') for x in (None,True,I(0),1.5,-1,1001)],
])
def test_records_invalid(rows,message):
    with pytest.raises(ValueError) as exc:assign_bands([1],rows)
    assert str(exc.value)==message


def test_caps_singletons_boundary_and_output_ownership():
    ts=list(range(1,20))+[1000];rows=[(str(i),1000) for i in range(100)];out=assign_bands(ts,rows);assert out['counts'][-1]==(20,100);out['bands'].clear();assert len(rows)==100
    assert assign_bands([1000],[('x'*80,1000)])['bands']==[('x'*80,1)]
    assert assign_bands([1],[('\u200b',0)])['bands']==[('\u200b',0)]
