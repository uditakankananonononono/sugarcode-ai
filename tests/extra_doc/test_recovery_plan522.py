import random,copy,itertools
import pytest
from sugarcode.extra_doc.recovery_plan522 import plan


def reference(ss,ds):
    candidates=[]
    for order in itertools.permutations(range(len(ss))):
        done=set();valid=True
        for i in order:
            if not set(ds[i]).issubset(done):valid=False;break
            done.add(i)
        if not valid:continue
        trace=[]
        for k,i in enumerate(order):
            start=sum(ss[j][0] for j in order[:k]);complete=start+ss[i][0]
            trace.append(dict(service=i,start=start,complete=complete,weighted_disruption=complete*ss[i][1]))
        candidates.append((sum(t['weighted_disruption'] for t in trace),order,trace))
    if not candidates:return None
    cost,order,trace=min(candidates)
    return dict(order=order,weighted_disruption=cost,timeline=trace,makespan=sum(d for d,w in ss),restoration_performed=False)


def test_reference():
    rng=random.Random(522)
    for _ in range(400):
        n=rng.randint(1,6);ss=[(rng.randint(1,20),rng.randint(1,1000)) for _ in range(n)];ds=[[j for j in range(i) if rng.random()<.3] for i in range(n)];b=copy.deepcopy((ss,ds));assert plan(ss,ds)==reference(ss,ds);assert (ss,ds)==b
    assert plan([(10,1),(1,100)],[[],[]])['order']==(1,0)
    assert plan([(10,1),(1,100)],[[],[0]])['order']==(0,1)


def test_caps():
    for d in (1,10**6):
        for w in (1,1000):assert plan([(d,w)],[[]])==reference([(d,w)],[[]])
    r=plan([(10**6,1000)]*8,[[]]*8);assert r['order']==tuple(range(8)) and r['weighted_disruption']==36*10**9 and r['makespan']==8*10**6
    with pytest.raises(ValueError,match='acyclic'):plan([(1,1)]*2,[[1],[0]])


@pytest.mark.parametrize('i,bad',[(i,b) for i in (0,1) for b in (True,1.0,'1',None)])
def test_types(i,bad):
    s=[1,1];s[i]=bad
    with pytest.raises(ValueError):plan([tuple(s)],[[]])


@pytest.mark.parametrize('ss,ds',[(None,[]),([],[]),([None]*9,[[]]*9),([(1,1)],None),([(1,1)],[]),([(1,1)],[None]),([(1,1)],[[0]*9]),([()],[[]]),([(1,)],[[]]),([(1,1,1)],[[]]),([[1,1]],[[]]),([(0,1)],[[]]),([(10**6+1,1)],[[]]),([(1,0)],[[]]),([(1,1001)],[[]]),([(1,1)],[[True]]),([(1,1)],[[1.0]]),([(1,1)],[['0']]),([(1,1)],[[None]]),([(1,1)],[[0]]),([(1,1)],[[-1]]),([(1,1)],[[1]]),([(1,1)]*2,[[],[0,0]]),([(1,1)]*2,[[],[0,True]])])
def test_refusals(ss,ds):
    with pytest.raises(ValueError):plan(ss,ds)


def test_preflight():
    with pytest.raises(ValueError,match='^service duration weight pair$'):plan([None]*8,[[0]*8]+[[]]*7)
    with pytest.raises(ValueError,match='^at most8 prerequisites before scan$'):plan([None]*8,[[0]*9]+[[]]*7)
    with pytest.raises(ValueError,match='^1..8 services before scan$'):plan([None]*9,[[]]*9)


class ListSubclass522(list):
    pass


class TupleSubclass522(tuple):
    pass


class IntSubclass522(int):
    pass


@pytest.mark.parametrize('bad', [(1,), (1, 1, 1), [1, 1], TupleSubclass522((1, 1))])
def test_pair_shape_exact_message_nonfirst(bad):
    with pytest.raises(ValueError, match='^service duration weight pair$'):
        plan([(1, 1), bad], [[], []])


@pytest.mark.parametrize('slot,message', [
    (0, '^duration integer1..1000000$'),
    (1, '^weight integer1..1000$'),
])
def test_integer_subclass_nonfirst(slot, message):
    row = [1, 1]
    row[slot] = IntSubclass522(1)
    with pytest.raises(ValueError, match=message):
        plan([(1, 1), tuple(row)], [[], []])


def test_container_and_prerequisite_subclasses_exact_messages():
    with pytest.raises(ValueError, match='^1..8 services before scan$'):
        plan(ListSubclass522([(1, 1)]), [[]])
    with pytest.raises(ValueError, match='^matching prerequisite lists$'):
        plan([(1, 1)], ListSubclass522([[]]))
    with pytest.raises(ValueError, match='^at most8 prerequisites before scan$'):
        plan([(1, 1), (1, 1)], [[], ListSubclass522([0])])
    with pytest.raises(ValueError, match='^valid nonself prerequisite indices$'):
        plan([(1, 1), (1, 1)], [[], [IntSubclass522(0)]])


def test_duplicate_prerequisite_exact_message_nonfirst():
    with pytest.raises(ValueError, match='^unique prerequisites$'):
        plan([(1, 1)] * 2, [[], [0, 0]])


def test_cycle_exact_message():
    with pytest.raises(ValueError, match='^prerequisites must be acyclic$'):
        plan([(1, 1)] * 2, [[1], [0]])
