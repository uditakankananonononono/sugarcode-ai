import random
import copy
import pytest
from sugarcode.extra_doc.bargaining1766 import select_offers
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass


def test_independent_gain_pair_dominance_oracle():
    rng=random.Random(1766)
    for _ in range(100):
        d=(rng.randrange(1001),rng.randrange(1001));rows=[(str(i),rng.randrange(1001),rng.randrange(1001)) for i in range(30)]
        gains=[(n,a-d[0],b-d[1]) for n,a,b in rows];valid=[(n,x*y) for n,x,y in gains if min(x,y)>=0]
        assert select_offers(d,rows)=={'products':valid,'maximizers':[n for n,p in valid if all(p>=q for m,q in valid)],'infeasible':[n for n,x,y in gains if min(x,y)<0],'claim':'PARTIAL','bargaining_validated':False}

@pytest.mark.parametrize('d',[
 None,[0,0],T((0,0)),(0,),(0,0,0),
 *[(x,0) for x in (None,True,I(0),1.5,-1,1001)],
 *[(0,x) for x in (None,True,I(0),1.5,-1,1001)],
])
def test_disagreement_invalid(d):
    with pytest.raises(ValueError) as exc:select_offers(d,[('a',0,0)])
    assert str(exc.value)=='disagreement must be a two-integer tuple in 0..1000'

@pytest.mark.parametrize('offers,message',[
 *[(x,'offers must be an exact list with 1..100 entries') for x in (None,L([('a',0,0)]),(('a',0,0),),[],[(str(i),0,0) for i in range(101)])],
 *[([x],'offer must be an id a b tuple') for x in (['a',0,0],T(('a',0,0)),('a',0),('a',0,0,1))],
 *[([(x,0,0)],'offer IDs must be unique nonblank exact strings of 1..80 characters') for x in (None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 ([('a',0,0),('a',1,1)],'offer IDs must be unique nonblank exact strings of 1..80 characters'),
 *[([('a',x,0)],'offer payoffs must be exact integers in 0..1000') for x in (None,True,I(0),1.5,-1,1001)],
 *[([('a',0,x)],'offer payoffs must be exact integers in 0..1000') for x in (None,True,I(0),1.5,-1,1001)],
])
def test_invalid(offers,message):
    with pytest.raises(ValueError) as exc:select_offers((0,0),offers)
    assert str(exc.value)==message


def test_caps_single_zero_gain_ties_and_no_feasible():
    assert len(select_offers((0,0),[(str(i),1000,1000) for i in range(100)])['maximizers'])==100
    assert select_offers((1000,1000),[('x'*80,1000,1000)])['products']==[('x'*80,0)]
    assert select_offers((1,1),[('\u200b',0,0)])['maximizers']==[]


def test_output_ownership():
    rows=[('a',1,1),('b',0,0)];before=copy.deepcopy(rows);out=select_offers((0,0),rows)
    for x in out.values():
        if type(x) is list:x.clear()
    assert rows==before
