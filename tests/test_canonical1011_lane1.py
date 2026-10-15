from itertools import product
from copy import deepcopy
import random
import pytest
from sugarcode.extra_doc import canonical1011 as m


def exact(a,b):
    assert type(a) is type(b)
    if type(b) is dict:
        assert list(a)==list(b)
        for k in b:exact(a[k],b[k])
    elif type(b) is bool:assert a is b
    else:assert a==b


def oracle(C):
    # Gaussian integer repeatedquarterturnrotation, notdirectiontable.
    real=imag=0
    for a,p in C:
        x,y=a,0
        for _ in range(p):x,y=-y,x
        real+=x;imag+=y
    return dict(real=real,imaginary=imag,squared_magnitude=real**2+imag**2,cancelled=not(real or imag),treatment_validated=False)


def test_gaussian_integer_rotation_oracle_purity():
    rng=random.Random(1011)
    for _ in range(600):
        C=tuple((rng.randint(0,8),rng.randint(0,3)) for i in range(4));old=deepcopy(C);exact(m.combine(C),oracle(C));assert C==old
    for phases in product(range(4),repeat=4):
        C=tuple((8,p) for p in phases);exact(m.combine(C),oracle(C))
    assert m.combine(((8,0),(8,2),(8,1),(8,3)))['cancelled'] is True
    assert m.combine(((8,0),)*4)['squared_magnitude']==1024


class I(int):pass
class T(tuple):pass


def test_caps_allslots_firstbad():
    def fail(C,msg):
        old=deepcopy(C)
        with pytest.raises(ValueError) as e:m.combine(C)
        assert str(e.value)==msg;assert C==old
    for C in (None,[],(),T(((0,0),)*4),((0,0),)*3,((0,0),)*5):fail(C,'channels exact tuple4')
    for i in range(4):
        for row in (None,[],(),T((0,0)),(0,),(0,0,0)):fail(((0,0),)*i+(row,)+(None,)*(3-i),'channel exact tuple2')
        for a in (None,True,I(0),0.0,-1,9):fail(((0,0),)*i+((a,None),)+(None,)*(3-i),'amplitude exact int0..8')
        for p in (None,True,I(0),0.0,-1,4):fail(((0,0),)*i+((0,p),)+(None,)*(3-i),'phase exact int0..3')
    assert m.SCOPE=='PARTIAL: caller four-channel integer quarter-turn phasor sum only'
    assert m.NOT_CLAIMED==('acoustic propagation','brain treatment','clinical safety')
