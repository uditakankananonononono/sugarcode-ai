import random,copy,itertools
import pytest
from sugarcode.extra_doc.support_routing448 import route


def reference(qs,ss):
    answers=[]
    for start in ss:
        candidates=[]
        rest=[i for i in range(len(qs)) if i!=start]
        for length in range(len(qs)):
            for tail in itertools.permutations(rest,length):
                path=(start,)+tail
                if any(path[k+1] not in qs[path[k]][1] for k in range(len(path)-1)):continue
                if qs[path[-1]][0] is not None:candidates.append((length+qs[path[-1]][0],path))
        if not candidates:answers.append(None)
        else:
            cost,path=min(candidates);answers.append(dict(path=path,cost=cost,terminal=path[-1]))
    return dict(routes=answers,infrastructure_created=False)


def test_reference():
    rng=random.Random(448)
    for _ in range(400):
        n=rng.randint(1,6);qs=[(rng.choice([None,0,rng.randint(0,8)]),[j for j in range(n) if rng.random()<.3]) for i in range(n)];ss=list(range(n));b=copy.deepcopy((qs,ss));assert route(qs,ss)==reference(qs,ss);assert (qs,ss)==b
    assert route([(None,[2,1]),(0,[]),(0,[])],[0])['routes']==[dict(path=(0,1),cost=1,terminal=1)]
    assert route([(10,[1]),(0,[0])],[0,1])==reference([(10,[1]),(0,[0])],[0,1])


def test_caps():
    for cost in (None,0,10**6):
        for n in (1,8):
            qs=[(cost,[]) for _ in range(n)]
            for ss in ([],[0]*64):assert route(qs,ss)==reference(qs,ss)
    q=[(None,list(range(8)))]+[(0,[]) for _ in range(7)]
    assert route(q,[0])==reference(q,[0])


@pytest.mark.parametrize('qs,ss',[(None,[]),([],[]),([(0,[])]*9,[]),([(0,[])],None),([(0,[])],[0]*65),([[0,[]]],[]),([(0,)],[]),([(0,[],None)],[]),([(0,None)],[]),([(0,[0]*9)],[]),([(True,[])],[]),([(1.0,[])],[]),([('0',[])],[]),([(-1,[])],[]),([(10**6+1,[])],[]),([(0,[True])],[]),([(0,[0,True])],[]),([(0,[-1])],[]),([(0,[1])],[]),([(0,[0,0])],[]),([(0,[])],[True]),([(0,[])],[0,True]),([(0,[])],[-1]),([(0,[])],[1]),([(0,[])],['0'])])
def test_refusals(qs,ss):
    with pytest.raises(ValueError):route(qs,ss)

@pytest.mark.parametrize('bad',[True,1.0,'0',None])
def test_slot_types(bad):
    if bad is not None:
        with pytest.raises(ValueError):route([(bad,[])],[])
    with pytest.raises(ValueError):route([(0,[bad])],[])
    with pytest.raises(ValueError):route([(0,[])],[bad])


def test_arity():
    for row in ((),(0,),(0,[],0),{0:0,1:[]}):
        with pytest.raises(ValueError):route([row],[])
