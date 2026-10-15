from itertools import product
from copy import deepcopy
import random
import pytest
from sugarcode.extra_doc import canonical2009 as m


def exact(a,b):
    assert type(a) is type(b)
    if type(b) is dict:
        assert list(a)==list(b)
        for k in b:exact(a[k],b[k])
    elif type(b) in (list,tuple):
        assert len(a)==len(b)
        for x,y in zip(a,b):exact(x,y)
    elif type(b) is bool:assert a is b
    else:assert a==b


def oracle(g,x,b,h):
    stages=[set() for t in range(h+1)];stages[0]={x}
    for path in product(range(-b,b+1),repeat=h):
        state=x
        for t,w in enumerate(path):state=g*state+w;stages[t+1].add(state)
    return dict(intervals=[(min(s),max(s)) for s in stages],terminal_count=len(stages[-1]),worst_absolute=max(abs(s) for s in stages[-1]),system_validated=False)


def test_independent_disturbance_paths_purity():
    rng=random.Random(2009)
    for _ in range(250):
        a=(rng.randint(-3,3),rng.randint(-4,4),rng.randint(0,3),rng.randint(0,5));old=deepcopy(a);exact(m.reach(*a),oracle(*a));assert a==old
    for a in ((-3,-4,3,5),(3,4,3,5),(0,4,3,5),(3,4,0,5),(-3,-4,3,0),(3,0,1,2)):exact(m.reach(*a),oracle(*a))
    assert m.reach(3,0,0,5)['terminal_count']==1


class I(int):pass


def test_caps_allslots_firstbad():
    for slot,name,lo,hi in ((0,'gain',-3,3),(1,'initial',-4,4),(2,'bound',0,3),(3,'horizon',0,5)):
        for v in (None,True,I(0),0.0,lo-1,hi+1):
            a=[0,0,0,0];a[slot]=v
            for later in range(slot+1,4):a[later]=None
            old=deepcopy(a)
            with pytest.raises(ValueError) as e:m.reach(*a)
            assert str(e.value)==name+' exact int'+str(lo)+'..'+str(hi);assert a==old
    assert m.SCOPE=='PARTIAL: caller bounded integer-disturbance scalar reachability extremes and state counts'
    assert m.NOT_CLAIMED==('real system safety','stability validation','measured dynamics')
