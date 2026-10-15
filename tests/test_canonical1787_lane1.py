from itertools import combinations,product
from copy import deepcopy
import random
import pytest
from sugarcode.extra_doc import canonical1787 as m


@pytest.fixture(autouse=True)
def pure(monkeypatch):
    orig=m.balance
    def checked(*a,**k):
        before=deepcopy((a,k))
        try:return orig(*a,**k)
        finally:assert (a,k)==before
    monkeypatch.setattr(m,'balance',checked)


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


def oracle(a):
    n=len(a);edges=[(i,j) for i in range(n) for j in range(i+1,n) if a[i][j]];solutions={}
    for k in range(len(edges)+1):
        for removed in combinations(edges,k):
            remaining=set(edges)-set(removed);colors={};components=[];valid=True
            for root in range(n):
                if root in colors:continue
                colors[root]=0;component=[];stack=[root]
                while stack:
                    i=stack.pop();component.append(i)
                    for u,v in remaining:
                        if i not in (u,v):continue
                        j=v if i==u else u;want=colors[i]^(a[u][v]<0)
                        if j in colors:
                            if colors[j]!=want:valid=False
                        else:colors[j]=want;stack.append(j)
                components.append(component)
            if not valid:continue
            for flips in product((0,1),repeat=len(components)-1):
                groups=[0]*n
                for c,flip in zip(components,(0,)+flips):
                    for i in c:groups[i]=colors[i]^flip
                solutions[tuple(groups)]=list(removed)
        if solutions:
            partitions=sorted(solutions);return dict(frustration_index=k,optimal_partitions=partitions,violated_edges=[solutions[p] for p in partitions],balanced=k==0,trust_validated=False)


def test_edgedeletion_component_parity_oracle():
    for n in range(2,4):
        edges=list(combinations(range(n),2))
        for signs in product((-1,0,1),repeat=len(edges)):
            a=[[0]*n for _ in range(n)]
            for (i,j),b in zip(edges,signs):a[i][j]=a[j][i]=b
            a=tuple(map(tuple,a));exact(m.balance(a),oracle(a))
    rng=random.Random(1787)
    for _ in range(150):
        a=[[0]*5 for _ in range(5)]
        for i,j in combinations(range(5),2):a[i][j]=a[j][i]=rng.choice((-1,0,1))
        a=tuple(map(tuple,a));exact(m.balance(a),oracle(a))
    out=m.balance(((0,-1,-1),(-1,0,-1),(-1,-1,0)));assert out['frustration_index']==1;assert len(out['optimal_partitions'])==3


class I(int):pass
class T(tuple):pass


def fail(a,msg):
    with pytest.raises(ValueError) as e:m.balance(a)
    assert str(e.value)==msg


def test_caps_slots_firstbad():
    for a in (None,[],T(((0,0),(0,0))),(),((0,),),((0,)*6,)*6):fail(a,'adjacency exact tuple2..5')
    for i in range(5):
        for row in (None,[],T((0,)*5),(),(0,)*4,(0,)*6):
            a=[(0,)*5]*5;a[i]=row;fail(tuple(a),'row exact tupleN')
        for j in range(5):
            for v in (None,True,I(0),0.0,-2,2):
                a=[[0]*5 for _ in range(5)];a[i][j]=v;fail(tuple(map(tuple,a)),'edge exact int-1/0/1')
    fail(((1,0),(1,0)),'diagonal must be zero');fail(((0,1),(0,0)),'adjacency must be symmetric');fail(((1,None),(0,0)),'edge exact int-1/0/1')
    for sign in (-1,1):
        a=tuple(tuple(sign if i!=j else 0 for j in range(5)) for i in range(5));exact(m.balance(a),oracle(a))
    assert m.SCOPE=='PARTIAL: caller signed-network frustration index and optimal balance partitions'
    assert m.NOT_CLAIMED==('verified trust','relationship inference','social diagnosis')
