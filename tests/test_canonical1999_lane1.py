from fractions import Fraction as F
from copy import deepcopy
import pytest
from sugarcode.extra_doc import canonical1999 as m


def oracle(n,k,r):
    # Build full transition matrix from independent birth/death outcomes.
    P=[[F(0)]*(n+1) for _ in range(n+1)]
    for i in range(1,n):
        for birth in (0,1):
            for death in (0,1):
                p=F(r*i if birth else n-i,r*i+n-i)*F(i if death else n-i,n);P[i][i+birth-death]+=p
    A=[[F(int(i==j))-P[i][j] for j in range(1,n)]+[P[i][n],F(1)] for i in range(1,n)]
    for c in range(n-1):
        pivot=next(i for i in range(c,n-1) if A[i][c]);A[c],A[pivot]=A[pivot],A[c];v=A[c][c];A[c]=[x/v for x in A[c]]
        for i in range(n-1):
            if i!=c:
                v=A[i][c];A[i]=[x-v*y for x,y in zip(A[i],A[c])]
    p,t=(F(0),F(0)) if k==0 else (F(1),F(0)) if k==n else A[k-1][-2:]
    return dict(fixation_probability=p,expected_absorption_steps=t,evolution_validated=False)


def exact(a,b):
    assert type(a) is type(b)
    if type(b) is dict:
        assert list(a)==list(b)
        for k in b:exact(a[k],b[k])
    elif type(b) is bool:assert a is b
    else:assert a==b


def test_full_markov_gaussian_oracle_purity():
    for n in range(2,9):
        for k in range(n+1):
            for r in range(1,5):
                a=(n,k,r);old=deepcopy(a);exact(m.fixation(*a),oracle(*a));assert a==old
        assert m.fixation(n,1,1)['fixation_probability']==F(1,n)
    assert m.fixation(2,1,1)['expected_absorption_steps']==2


class I(int):pass


def test_all_caps_slots_firstbad():
    def fail(a,msg):
        with pytest.raises(ValueError) as e:m.fixation(*a)
        assert str(e.value)==msg
    for n in (None,True,I(2),2.0,1,9):fail((n,None,None),'population exact int2..8')
    for n in range(2,9):
        for k in (None,True,I(0),0.0,-1,n+1):fail((n,k,None),'mutants exact int0..'+str(n))
    for r in (None,True,I(1),1.0,0,5):fail((8,8,r),'fitness exact int1..4')
    assert m.SCOPE=='PARTIAL: caller finite Moran chain fixation and absorption expectations'
    assert m.NOT_CLAIMED==('real biological fitness','evolution prediction','measured population')
