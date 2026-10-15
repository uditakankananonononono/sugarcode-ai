from copy import deepcopy
import random
import pytest
from sugarcode.extra_doc import canonical1012 as m


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


def oracle(C,x,H,L,P):
    bucket=[1]*x;res=[];sent=[];spill=[];lost=[]
    for h in H:
        loss=0
        for i in range(L):
            if bucket:bucket.pop();loss+=1
        overflow=0
        for i in range(h):
            if len(bucket)<C:bucket.append(1)
            else:overflow+=1
        n=0
        while len(bucket)>=P:
            for i in range(P):bucket.pop()
            n+=1
        res.append(len(bucket));sent.append(n);spill.append(overflow);lost.append(loss)
    return dict(charge=tuple(res),packets=tuple(sent),spill=tuple(spill),leak_loss=tuple(lost),sensor_validated=False)


def test_unit_energy_bucket_oracle_purity():
    rng=random.Random(1012)
    for _ in range(750):
        C=rng.randint(1,16);a=(C,rng.randint(0,C),tuple(rng.randint(0,8) for i in range(8)),rng.randint(0,4),rng.randint(1,8));old=deepcopy(a);exact(m.telemetry(*a),oracle(*a));assert a==old
    for C in (1,16):
        for L in (0,4):
            for P in (1,8):
                for H in ((0,)*8,(8,)*8):exact(m.telemetry(C,C,H,L,P),oracle(C,C,H,L,P))
    assert m.telemetry(16,16,(8,)*8,0,8)['spill'][0]==8


class I(int):pass
class T(tuple):pass


def test_caps_allslots_firstbad():
    def fail(a,msg):
        old=deepcopy(a)
        with pytest.raises(ValueError) as e:m.telemetry(*a)
        assert str(e.value)==msg;assert a==old
    for C in (None,True,I(1),1.0,0,17):fail((C,None,None,None,None),'capacity exact int1..16')
    for C in range(1,17):
        for x in (None,True,I(0),0.0,-1,C+1):fail((C,x,None,None,None),'initial exact int0..capacity')
    for H in (None,[],(),T((0,)*8),(0,)*7,(0,)*9):fail((16,0,H,None,None),'harvest exact tuple8')
    for i in range(8):
        for v in (None,True,I(0),0.0,-1,9):fail((16,0,(0,)*i+(v,)+(None,)*(7-i),None,None),'harvest exact int0..8')
    for L in (None,True,I(0),0.0,-1,5):fail((16,0,(0,)*8,L,None),'leak exact int0..4')
    for P in (None,True,I(1),1.0,0,9):fail((16,0,(0,)*8,0,P),'packet exact int1..8')
    assert m.SCOPE=='PARTIAL: caller eight-slot integer harvest-leak packet energy bucket'
    assert m.NOT_CLAIMED==('neural sensing','biomedical device feasibility','measured energy')
