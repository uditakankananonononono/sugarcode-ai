from copy import deepcopy
import pytest
from sugarcode.extra_doc import canonical2012 as m


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


def oracle(n,s):
    states=[(2**t*s)%n for t in range(n+1)]
    stop=next(t for t in range(1,n+1) if states[t] in states[:t]);first=states[:stop].index(states[stop]);cycle=tuple(states[first:stop])
    return dict(transient=tuple(states[:first]),cycle=cycle,first_repeat_step=stop,return_period=len(cycle) if first==0 else None,chaos_validated=False)


def test_all528_modular_power_orbits_purity():
    for n in range(1,33):
        for s in range(n):
            a=(n,s);old=deepcopy(a);exact(m.orbit(*a),oracle(*a));assert a==old
    assert m.orbit(8,1)['transient']==(1,2,4)
    assert m.orbit(7,1)['cycle']==(1,2,4)
    assert m.orbit(1,0)['return_period']==1


class I(int):pass


def test_caps_allslots_firstbad():
    def fail(a,msg):
        old=deepcopy(a)
        with pytest.raises(ValueError) as e:m.orbit(*a)
        assert str(e.value)==msg;assert a==old
    for n in (None,True,I(1),1.0,0,33):fail((n,None),'modulus exact int1..32')
    for n in range(1,33):
        for s in (None,True,I(0),0.0,-1,n):fail((n,s),'start exact int0..modulus-1')
    assert m.SCOPE=='PARTIAL: caller finite modular doubling orbit transient, cycle and return period'
    assert m.NOT_CLAIMED==('continuous chaos','Lyapunov exponent','physical prediction')
