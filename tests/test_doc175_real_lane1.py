"""Full interaction normal-equation oracle, not groupwise fits."""
from fractions import Fraction as F
from copy import deepcopy
import random
import pytest
from sugarcode.extra_doc import moderation175 as m


@pytest.fixture(autouse=True)
def pure(monkeypatch):
    original=m.fit
    def checked(*args,**kwargs):
        before=deepcopy((args,kwargs))
        try:return original(*args,**kwargs)
        finally:assert (args,kwargs)==before
    monkeypatch.setattr(m,'fit',checked)


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


def oracle(rows):
    design=[(1,x,z,x*z) for x,z,y in rows];ys=[y for x,z,y in rows]
    a=[[F(sum(r[i]*r[j] for r in design)) for j in range(4)]+[F(sum(r[i]*y for r,y in zip(design,ys)))] for i in range(4)]
    for k in range(4):
        pivot=next(i for i in range(k,4) if a[i][k]);a[k],a[pivot]=a[pivot],a[k]
        scale=a[k][k];a[k]=[v/scale for v in a[k]]
        for i in range(4):
            if i!=k:
                scale=a[i][k];a[i]=[v-scale*w for v,w in zip(a[i],a[k])]
    c=tuple(row[-1] for row in a)
    residual=[F(y)-sum(v*w for v,w in zip(c,r)) for r,y in zip(design,ys)]
    return dict(coefficients=c,group_lines=[(c[0],c[1]),(c[0]+c[2],c[1]+c[3])],
                crossover=-c[2]/c[3] if c[3] else None,sse=sum((v*v for v in residual),F(0)),causal_moderation_identified=False)


def test_full_interaction_regression_oracle():
    rng=random.Random(175)
    for _ in range(400):
        rows=[(-1,0,rng.randint(-5,5)),(1,0,rng.randint(-5,5)),(-1,1,rng.randint(-5,5)),(1,1,rng.randint(-5,5))]
        rows += [(rng.randint(-5,5),rng.randrange(2),rng.randint(-5,5)) for _ in range(rng.randrange(5))]
        rng.shuffle(rows);expected=oracle(rows);exact(m.fit(rows),expected)
    exact(m.fit([(0,0,1),(1,0,2),(0,1,3),(1,1,2)]),dict(coefficients=(F(1),F(1),F(2),F(-2)),
          group_lines=[(F(1),F(1)),(F(3),F(-1))],crossover=F(1),sse=F(0),causal_moderation_identified=False))
    for v in (-5,5):
        rows=[(-5,0,v),(5,0,v),(-5,1,-v),(5,1,-v)]*2
        exact(m.fit(rows),oracle(rows));assert m.fit(rows)['crossover'] is None


class I(int):pass
class L(list):pass
class T(tuple):pass


def fail(rows,msg):
    with pytest.raises(ValueError) as exc:m.fit(rows)
    assert str(exc.value)==msg


def test_guards_caps_first_bad():
    for x in (None,(),L([(0,0,0)]*4),[],[(0,0,0)]*3,[(0,0,0)]*9):fail(x,'rows must be exact list4..8')
    for i in range(8):
        for x in (None,[],T((0,0,0)),(),(0,0),(0,0,0,0)):
            rows=[(0,0,0)]*8;rows[i]=x;fail(rows,'row must be exact X Z Y triple tuple')
        for j,name,low,high in ((0,'X',-5,5),(1,'Z',0,1),(2,'Y',-5,5)):
            for x in (True,1.0,I(1),None,low-1,high+1):
                row=[0]*3;row[j]=x;rows=[(0,0,0)]*8;rows[i]=tuple(row)
                fail(rows,name+' must be exact int'+str(low)+'..'+str(high))
    fail([(0,0,True),None,(0,0,0),(0,0,0)],'Y must be exact int-5..5')
    fail([(0,True,None),None,(0,0,0),(0,0,0)],'Z must be exact int0..1')
    fail([(0,0,0)]*4,'group0 must contain distinct X values')
    fail([(-1,0,0),(1,0,0),(0,1,0),(0,1,0)],'group1 must contain distinct X values')
    fail([(0,0,0)]*3+[(0,0,True)],'Y must be exact int-5..5')
    assert m.SCOPE=='PARTIAL: exact binary-moderator OLS slope heterogeneity and line crossover'
    assert m.NOT_CLAIMED==('causal moderation','significance testing','continuous moderators','measurement validity','sampling uncertainty')
