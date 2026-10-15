"""Independent pairwise weighted covariance identity oracle."""
from fractions import Fraction as F
from itertools import combinations
import random
import pytest
from sugarcode.extra_doc import rd171 as m


def exact(a,b):
    assert type(a) is type(b)
    if type(b) is dict:
        assert list(a)==list(b)
        for k in b:exact(a[k],b[k])
    elif type(b) in (tuple,list):
        assert len(a)==len(b)
        for x,y in zip(a,b):exact(x,y)
    elif type(b) is bool:assert a is b
    else:assert a==b


def oracle(c,h,rows):
    groups=[];fits=[]
    for left in (True,False):
        indices=tuple(i for i,(x,y) in enumerate(rows) if c-h<x<c+h and (x<c)==left)
        points=[(rows[i][0]-c,rows[i][1],h-abs(rows[i][0]-c)) for i in indices]
        den=sum(w*v*(x-z)**2 for (x,y,w),(z,t,v) in combinations(points,2))
        if den:
            slope=F(sum(w*v*(x-z)*(y-t) for (x,y,w),(z,t,v) in combinations(points,2)),den)
            intercept=F(sum(w*(y-slope*x) for x,y,w in points),sum(w for x,y,w in points))
            fits.append((intercept,slope))
        else:fits.append(None)
        groups.append(indices)
    return dict(left=fits[0],right=fits[1],jump=fits[1][0]-fits[0][0] if None not in fits else None,
                used=groups,causality_identified=False)


def test_pairwise_oracle():
    rng=random.Random(171)
    for _ in range(450):
        c=rng.randint(-5,5);h=rng.randint(1,5)
        rows=[(rng.randint(-5,5),rng.randint(-5,5)) for _ in range(rng.randint(1,8))]
        exact(m.estimate(c,h,rows),oracle(c,h,rows))
    rows=[(-2,-1),(-1,1),(0,4),(1,5)]
    exact(m.estimate(0,3,rows),dict(left=(F(3),F(2)),right=(F(4),F(1)),jump=F(1),used=[(0,1),(2,3)],causality_identified=False))
    for c in (-5,5):
        for h in (1,5):
            rows=[(-5,-5),(5,5)]*4;exact(m.estimate(c,h,rows),oracle(c,h,rows))
    # Kernel weights change a non-collinear side's fitted cutoff intercept.
    rows=[(-3,-5),(-2,1),(-1,1),(0,0),(1,1),(2,5)]
    exact(m.estimate(0,4,rows),oracle(0,4,rows))
    assert m.estimate(0,1,[(0,0),(1,1),(-1,-1)])['used']==[(),(0,)]
    assert m.estimate(0,5,[(1,0),(1,1)])['right'] is None


class I(int):pass
class L(list):pass
class T(tuple):pass


def fail(c,h,rows,message):
    with pytest.raises(ValueError) as exc:m.estimate(c,h,rows)
    assert str(exc.value)==message


def test_validation_caps_and_order():
    for x in (True,1.0,I(1),None,-6,6):fail(x,None,None,'cutoff must be exact int-5..5')
    for x in (True,1.0,I(1),None,0,6):fail(0,x,None,'bandwidth must be exact int1..5')
    for x in (None,(),L([(0,0)]),[],[(0,0)]*9):fail(0,1,x,'rows must be exact list1..8')
    for pos in range(8):
        for x in (None,[],T((0,0)),(),(0,),(0,0,0)):
            rows=[(0,0)]*8;rows[pos]=x;fail(0,1,rows,'row must be exact running outcome pair tuple')
        for x in (True,1.0,I(1),None,-6,6):
            rows=[(0,0)]*8;rows[pos]=(x,None);fail(0,1,rows,'running must be exact int-5..5')
            rows=[(0,0)]*8;rows[pos]=(0,x);fail(0,1,rows,'outcome must be exact int-5..5')
    fail(0,1,[(0,True),None],'outcome must be exact int-5..5')
    fail(0,1,[(True,None),None],'running must be exact int-5..5')
    assert m.SCOPE=='PARTIAL: exact triangular-kernel local-linear sharp-cutoff discontinuity'
    assert m.NOT_CLAIMED==('causal identification','continuity assumptions','bandwidth selection',
                           'manipulation diagnosis','sampling uncertainty')
