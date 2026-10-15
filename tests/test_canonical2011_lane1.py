from fractions import Fraction as F
from itertools import combinations,product
from copy import deepcopy
import random
import pytest
from sugarcode.extra_doc import canonical2011 as m


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


def oracle(W):
    E=((0,1),(0,2),(0,3),(1,2),(1,3),(2,3));records=[]
    for chosen in combinations(range(6),3):
        seen={0}
        for _ in range(4):
            for i in chosen:
                a,b=E[i]
                if a in seen or b in seen:seen|={a,b}
        if len(seen)!=4:continue
        weight=1
        for i in chosen:weight*=W[i]
        records.append((chosen,weight))
    Z=sum(w for c,w in records)
    return dict(partition=Z,edge_probabilities=tuple(F(sum(w for c,w in records if i in c),Z) if Z else None for i in range(6)),network_validated=False)


def test_all20_edge_triples_oracle_purity():
    rng=random.Random(2011)
    for _ in range(550):
        W=tuple(rng.randint(0,3) for i in range(6));old=deepcopy(W);exact(m.trees(W),oracle(W));assert W==old
    for W in product((0,3),repeat=6):exact(m.trees(W),oracle(W))
    assert m.trees((1,)*6)['partition']==16
    assert m.trees((1,)*6)['edge_probabilities']==(F(1,2),)*6
    assert m.trees((0,)*6)['edge_probabilities']==(None,)*6


class I(int):pass
class T(tuple):pass


def test_caps_allslots_firstbad():
    def fail(W,msg):
        old=deepcopy(W)
        with pytest.raises(ValueError) as e:m.trees(W)
        assert str(e.value)==msg;assert W==old
    for W in (None,[],(),T((0,)*6),(0,)*5,(0,)*7):fail(W,'weights exact tuple6')
    for i in range(6):
        for v in (None,True,I(0),0.0,-1,4):fail((0,)*i+(v,)+(None,)*(5-i),'weight exact int0..3')
    assert m.SCOPE=='PARTIAL: caller four-node weighted spanning-tree partition and edge inclusion law'
    assert m.NOT_CLAIMED==('real network robustness','physical resistance','measured network')
