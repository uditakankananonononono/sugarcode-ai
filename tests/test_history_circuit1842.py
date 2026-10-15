import copy,itertools,random,pytest
from sugarcode.extra_doc import history_circuit1842 as m
class L(list):pass
class T(tuple):pass
class I(int):pass

def check(nodes):
    def solve(i,fixed=None,value=0):
        if i==fixed:return value
        op,a,b=nodes[i]
        if op<2:return op
        x,y=solve(a,fixed,value),solve(b,fixed,value)
        return int(x and y) if op==2 else int(x or y) if op==3 else int(x!=y)
    expected=dict(baseline=[solve(i) for i in range(len(nodes))],intervention_targets=[[solve(len(nodes)-1,i,0),solve(len(nodes)-1,i,1)] for i in range(len(nodes))],history_validated=False)
    old=copy.deepcopy(nodes);out=m.evaluate(nodes);assert out==expected and nodes==old
    assert type(out) is dict and list(out)==list(expected) and out['history_validated'] is False
    assert type(out['baseline']) is list and all(type(x) is int for x in out['baseline'])
    assert type(out['intervention_targets']) is list and all(type(r) is list and all(type(x) is int for x in r) for r in out['intervention_targets'])
def test_recursive_equations():
    for n in range(1,4):
        menus=[[(0,0,0),(1,0,0)]+[(op,a,b) for op in (2,3,4) for a,b in itertools.product(range(i),repeat=2)] for i in range(n)]
        for nodes in itertools.product(*menus):check(list(nodes))
    rng=random.Random(1842)
    for _ in range(1000):
        nodes=[]
        for i in range(rng.randint(1,6)):
            op=rng.randrange(5) if i else rng.randrange(2)
            nodes.append((op,0,0) if op<2 else (op,rng.randrange(i),rng.randrange(i)))
        check(nodes)
    assert m.SCOPE=='PARTIAL: supplied acyclic binary circuit single-node intervention arithmetic'
    assert m.NOT_CLAIMED==('historical causality','counterfactual validity','real history','production readiness')
def test_validation():
    for n in (None,(),L([(0,0,0)]),[],[(0,0,0)]*7):
        with pytest.raises(ValueError,match=r'^nodes exact list1\.\.6$'):m.evaluate(n)
    for row in (None,[],T((0,0,0)),(),(0,),(0,0,0,0)):
        with pytest.raises(ValueError,match='^node exact tuple3$'):m.evaluate([row])
    for op in (-1,5,True,I(0),0.0,None):
        with pytest.raises(ValueError,match=r'^operation exact int0\.\.4$'):m.evaluate([(op,None,None)])
    for col in (1,2):
        for x in (True,I(0),0.0,None):
            row=[0,0,0];row[col]=x
            with pytest.raises(ValueError,match='^arguments exact integers$'):m.evaluate([tuple(row)])
    with pytest.raises(ValueError,match='^constant arguments must0$'):m.evaluate([(0,1,0)])
    with pytest.raises(ValueError,match='^constant arguments must0$'):m.evaluate([(0,0,1)])
    with pytest.raises(ValueError,match='^constant arguments must0$'):m.evaluate([(1,0,2)])
    for row in ((2,0,0),(3,-1,0),(4,0,1)):
        with pytest.raises(ValueError,match='^arguments must reference earlier nodes$'):m.evaluate([row])
    for row in ((2,1,0),(2,0,1),(2,-1,0),(2,0,-1)):
        with pytest.raises(ValueError,match='^arguments must reference earlier nodes$'):m.evaluate([(0,0,0),row])
