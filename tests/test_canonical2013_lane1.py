from copy import deepcopy
import random
import pytest
from sugarcode.extra_doc import canonical2013 as m


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


def oracle(M,d):
    n=3**d;points=set()
    for r in range(n):
        for c in range(n):
            occupied=True;x,y=r,c
            for k in range(d):
                if not M[(x%3)*3+y%3]:occupied=False
                x//=3;y//=3
            if occupied:points.add((r,c))
    grid=tuple(tuple(int((r,c) in points) for c in range(n)) for r in range(n));counts=tuple(len({(r//(3**level),c//(3**level)) for r,c in points}) for level in range(d+1))
    return dict(grid=grid,occupied=len(points),box_counts=counts,geometry_validated=False)


def test_base3_digit_membership_oracle_purity():
    rng=random.Random(2013)
    for _ in range(220):
        M=tuple(rng.randrange(2) for i in range(9));d=rng.randint(0,3);a=(M,d);old=deepcopy(a);exact(m.refine(*a),oracle(*a));assert a==old
    for M in ((0,)*9,(1,)*9,(1,1,1,1,0,1,1,1,1)):
        for d in range(4):exact(m.refine(M,d),oracle(M,d))
    assert m.refine((1,1,1,1,0,1,1,1,1),3)['occupied']==512
    assert m.refine((1,)*9,3)['box_counts']==(729,81,9,1)


class I(int):pass
class T(tuple):pass


def test_caps_allslots_firstbad():
    def fail(M,d,msg):
        old=deepcopy((M,d))
        with pytest.raises(ValueError) as e:m.refine(M,d)
        assert str(e.value)==msg;assert (M,d)==old
    for M in (None,[],(),T((0,)*9),(0,)*8,(0,)*10):fail(M,None,'mask exact tuple9')
    for i in range(9):
        for v in (None,True,I(0),0.0,-1,2):fail((0,)*i+(v,)+(None,)*(8-i),None,'mask exact bits')
    for d in (None,True,I(0),0.0,-1,4):fail((0,)*9,d,'depth exact int0..3')
    assert m.SCOPE=='PARTIAL: caller finite ternary self-similar mask grid and aligned box counts'
    assert m.NOT_CLAIMED==('Hausdorff dimension','infinite fractal','natural geometry')
