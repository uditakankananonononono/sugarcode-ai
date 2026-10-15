"""Directed path expansion oracle, independent of covariance recursion."""
from fractions import Fraction as F
from itertools import combinations
from copy import deepcopy
import random
import pytest
from sugarcode.extra_doc import sem176 as m


@pytest.fixture(autouse=True)
def pure(monkeypatch):
    original=m.imply
    def checked(*args,**kwargs):
        before=deepcopy((args,kwargs))
        try:return original(*args,**kwargs)
        finally:assert (args,kwargs)==before
    monkeypatch.setattr(m,'imply',checked)


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


def oracle(b,v):
    n=len(b);a=[[F(int(i==j)) for j in range(n)] for i in range(n)]
    for source in range(n):
        for target in range(source+1,n):
            for size in range(target-source):
                for middle in combinations(range(source+1,target),size):
                    path=(source,)+middle+(target,);weight=1
                    for j,k in zip(path,path[1:]):weight*=b[k][j]
                    a[target][source]+=weight
    c=[tuple(sum((a[i][k]*v[k]*a[j][k] for k in range(n)),F(0)) for j in range(n)) for i in range(n)]
    return dict(total_effects=[tuple(row) for row in a],covariance=c,model_validated=False)


def test_directed_path_oracle():
    rng=random.Random(176)
    for n in range(1,5):
        for _ in range(100):
            b=[tuple(rng.randint(-2,2) if j<i else 0 for j in range(n)) for i in range(n)]
            v=tuple(rng.randint(0,4) for _ in range(n));expected=oracle(b,v)
            exact(m.imply(b,v),expected)
    b=[(0,0,0),(2,0,0),(-1,1,0)]
    exact(m.imply(b,(1,2,3)),dict(total_effects=[(F(1),F(0),F(0)),(F(2),F(1),F(0)),(F(1),F(1),F(1))],
          covariance=[(F(1),F(2),F(1)),(F(2),F(6),F(4)),(F(1),F(4),F(6))],model_validated=False))
    for value in (-2,2):
        b=[tuple(value if j<i else 0 for j in range(4)) for i in range(4)]
        for var in (0,4):exact(m.imply(b,(var,)*4),oracle(b,(var,)*4))


class I(int):pass
class L(list):pass
class T(tuple):pass


def fail(b,v,message):
    with pytest.raises(ValueError) as exc:m.imply(b,v)
    assert str(exc.value)==message


def test_caps_types_and_first_bad():
    for x in (None,(),L([(0,)]),[],[(0,)*5]*5):fail(x,None,'coefficients must be exact list1..4')
    for x in (None,[],T((0,)),(),(0,0)):fail([None],x,'variances must be exact tuple of node count')
    for i in range(4):
        for x in (None,[],T((0,)*4),(),(0,)*3,(0,)*5):
            b=[(0,)*4]*4;b[i]=x;fail(b,(0,)*4,'coefficient row must be exact tuple of node count')
        for j in range(4):
            for x in (True,1.0,I(1),None,-3,3):
                row=[0]*4;row[j]=x;b=[(0,)*4]*4;b[i]=tuple(row)
                fail(b,(0,)*4,'coefficients must be exact ints-2..2')
            if j>=i:
                for x in (-2,-1,1,2):
                    row=[0]*4;row[j]=x;b=[(0,)*4]*4;b[i]=tuple(row)
                    fail(b,(0,)*4,'diagonal and upper coefficients must be zero')
        for x in (True,1.0,I(1),None,-1,5):
            v=[0]*4;v[i]=x;fail([(0,)*4]*4,tuple(v),'variances must be exact ints0..4')
    fail([(True,0),None],(0,0),'coefficients must be exact ints-2..2')
    fail([(1,True),None],(0,0),'diagonal and upper coefficients must be zero')
    fail([(0,0),None],(True,0),'coefficient row must be exact tuple of node count')
    assert m.SCOPE=='PARTIAL: exact recursive linear SEM total effects and implied covariance'
    assert m.NOT_CLAIMED==('parameter estimation','causal identification','model validity','correlated errors','cyclic equations')
