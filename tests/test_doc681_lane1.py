import random
import pytest
from sugarcode.extra_doc.onion681 import audit


def test_independent_boolean_matrix_closure_oracle():
    rng=random.Random(681)
    for _ in range(120):
        ids=[str(i) for i in range(6)];layers={n:rng.randrange(4) for n in ids}
        edges=[(a,b) for a in ids for b in ids if rng.randrange(4)==0]
        matrix=[[False]*6 for _ in range(6)]
        for a,b in edges:matrix[int(a)][int(b)]=True
        for k in range(6):
            for i in range(6):
                for j in range(6):matrix[i][j]=matrix[i][j] or matrix[i][k] and matrix[k][j]
        expected=[]
        for i,n in enumerate(ids):
            outer=[m for j,m in enumerate(ids) if j!=i and matrix[i][j] and layers[m]>layers[n]]
            if outer:expected.append((n,outer))
        got=audit(layers,edges)
        assert got['outward_reachability']==expected
        assert got['cyclic_modules']==[n for i,n in enumerate(ids) if matrix[i][i]]
        assert got['claim']=='PARTIAL' and got['code_validated'] is False

class D(dict):pass
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass

@pytest.mark.parametrize('layers,edges,message',[
 (D(a=0),[],'layers must be an exact dict with 1..50 entries'),
 ({},[],'layers must be an exact dict with 1..50 entries'),
 *[({x:0},[],'IDs must be nonblank exact strings of 1..80 characters') for x in (S('a'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 *[({'a':x},[],'layers must be integers in 0..10') for x in (True,I(0),-1,11)],
 ({'a':0},L(),'edges must be an exact list with 0..200 entries'),
 ({'a':0},[T(('a','a'))],'edges must be exact known ID pair tuples'),
 ({'a':0},[(S('a'),'a')],'edges must be exact known ID pair tuples'),
 ({'a':0},[('a','b')],'edges must be exact known ID pair tuples'),
])
def test_invalid(layers,edges,message):
    with pytest.raises(ValueError) as exc:audit(layers,edges)
    assert str(exc.value)==message


def test_chain_bounds_zero_width():
    layers={str(i):i%11 for i in range(50)};edges=[(str(i),str(i+1)) for i in range(49)]
    assert audit(layers,edges)['cyclic_modules']==[]
    assert audit({'x'*80:0,'\u200b':10},[('x'*80,'\u200b')]*200)['outward_reachability']==[('x'*80,['\u200b'])]
    assert audit({'a':0},[('a','a')])['cyclic_modules']==['a']
