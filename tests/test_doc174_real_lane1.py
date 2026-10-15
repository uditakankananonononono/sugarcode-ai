"""Centered covariance oracle, independent of normal-equation solver."""
from fractions import Fraction as F
from copy import deepcopy
import random
import pytest
from sugarcode.extra_doc import mediation174 as m


@pytest.fixture(autouse=True)
def no_mutation(monkeypatch):
    original=m.decompose
    def checked(*args,**kwargs):
        before=deepcopy((args,kwargs))
        try:return original(*args,**kwargs)
        finally:assert (args,kwargs)==before
    monkeypatch.setattr(m,'decompose',checked)


def exact(a,b):
    assert type(a) is type(b)
    if type(b) is dict:
        assert list(a)==list(b)
        for k in b:exact(a[k],b[k])
    elif type(b) is tuple:
        assert len(a)==len(b)
        for x,y in zip(a,b):exact(x,y)
    elif type(b) is bool:assert a is b
    else:assert a==b


def oracle(rows):
    n=len(rows);means=[F(sum(row[j] for row in rows),n) for j in range(3)]
    x,med,y=[[row[j]-means[j] for row in rows] for j in range(3)]
    xx=sum(v*v for v in x);mm=sum(v*v for v in med);xm=sum(a*b for a,b in zip(x,med))
    xy=sum(a*b for a,b in zip(x,y));my=sum(a*b for a,b in zip(med,y))
    det=xx*mm-xm*xm
    if not det:return None
    direct=(xy*mm-my*xm)/det;b=(my*xx-xy*xm)/det;a=xm/xx;c=xy/xx
    return dict(mediator_fit=(means[1]-a*means[0],a),
                outcome_fit=(means[2]-direct*means[0]-b*means[1],direct,b),
                total_fit=(means[2]-c*means[0],c),indirect=a*b,direct=direct,
                decomposition_residual=c-direct-a*b,causal_mediation_identified=False)


def test_centered_covariance_oracle():
    rng=random.Random(174)
    for _ in range(400):
        rows=[tuple(rng.randint(-5,5) for _ in range(3)) for _ in range(rng.randint(3,8))]
        expected=oracle(rows)
        if expected is None:
            with pytest.raises(ValueError,match='full column rank'):m.decompose(rows)
        else:exact(m.decompose(rows),expected)
    rows=[(0,0,-1),(1,1,1),(2,1,2),(3,3,5)]
    exact(m.decompose(rows),dict(mediator_fit=(F(-1,10),F(9,10)),outcome_fit=(F(-1),F(1),F(1)),
                                 total_fit=(F(-11,10),F(19,10)),indirect=F(9,10),direct=F(1),
                                 decomposition_residual=F(0),causal_mediation_identified=False))
    for v in (-5,5):
        rows=[(-5,-5,v),(5,-5,-v),(-5,5,v),(5,5,-v)]*2
        exact(m.decompose(rows),oracle(rows))
    for rows in ([ (0,0,0)]*3,[(i,i,0) for i in (-1,0,1)]):
        with pytest.raises(ValueError,match='full column rank'):m.decompose(rows)


class I(int):pass
class L(list):pass
class T(tuple):pass


def fail(rows,message):
    with pytest.raises(ValueError) as exc:m.decompose(rows)
    assert str(exc.value)==message


def test_types_caps_first_bad():
    for x in (None,(),L([(0,0,0)]*3),[],[(0,0,0)]*2,[(0,0,0)]*9):fail(x,'rows must be exact list3..8')
    for pos in range(8):
        for x in (None,[],T((0,0,0)),(),(0,0),(0,0,0,0)):
            rows=[(0,0,0)]*8;rows[pos]=x;fail(rows,'row must be exact X M Y triple tuple')
        for j in range(3):
            for x in (True,1.0,I(1),None,-6,6):
                row=[0]*3;row[j]=x;rows=[(0,0,0)]*8;rows[pos]=tuple(row)
                fail(rows,'values must be exact ints-5..5')
    fail([(0,0,True),None,(0,0,0)],'values must be exact ints-5..5')
    fail([(0,0,0)]*2+[(0,0,True)],'values must be exact ints-5..5')
    assert m.SCOPE=='PARTIAL: exact supplied-data linear OLS single-mediator coefficient decomposition'
    assert m.NOT_CLAIMED==('causal mediation','sequential ignorability','measurement validity','sampling uncertainty','nonlinear effects')
