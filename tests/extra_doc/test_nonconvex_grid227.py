import copy
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.nonconvex_grid227 import explore


def test_hand_nonconvex_two_basins_and_budget_trace_and_ties():
    a=[[[-2,-1,0,1,2]],[.5],0,[[0],[2],[4]],10];before=copy.deepcopy(a);r=explore(*a)
    assert [x['indices'] for x in r['runs']]==[[1],[1],[3]]
    assert [x['objective_fraction'] for x in r['runs']]==['-1/2','-1/2','1/2']
    assert r['runs'][0]['index_trace']==[[0],[1]] and r['runs'][0]['objective_trace_fraction']==['8','-1/2']
    assert r['winner_index']==0 and r['grid_vertex_count']==5 and not r['global_grid_optimum_claimed'] and not r['global_continuous_optimum_claimed'] and r['external_effects']==[] and a==before
    assert r['runs'][2]['point_fraction']==['1'] and r['runs'][0]['moves_used']==1 and r['runs'][0]['local_minimum_observed']
    assert not explore(*a[:4],1)['runs'][0]['local_minimum_observed']
    assert explore([[0]],[0],0,[[0]],1)['runs'][0]['local_minimum_observed']


def test_400_independent_whole_grid_neighbor_lookup_references():
    from itertools import product
    from random import Random
    rng=Random(227)
    for _ in range(400):
        d=rng.randrange(1,5);axes=[sorted(rng.sample(range(-3,4),rng.randrange(1,5))) for i in range(d)];linear=[rng.randrange(-3,4) for i in range(d)];coupling=rng.randrange(-3,4);starts=[[rng.randrange(len(axis)) for axis in axes] for j in range(3)];budget=rng.randrange(1,7)
        scores={}
        for p in product(*(range(len(a)) for a in axes)):
            x=[F(axes[i][j]) for i,j in enumerate(p)];scores[p]=sum(xi**4-2*xi**2+1+linear[i]*xi for i,xi in enumerate(x))+sum(coupling*x[i-1]*x[i] for i in range(1,d))
        expected=[]
        for start in starts:
            trace=[tuple(start)];local=False
            for i in range(budget):
                cur=trace[-1];adj=[p for p in scores if sum(abs(a-b) for a,b in zip(p,cur))==1];best=min(adj,key=lambda p:(scores[p],p)) if adj else cur
                if scores[best]>=scores[cur]:local=True;break
                trace.append(best)
            expected.append((trace,local))
        r=explore(axes,linear,coupling,starts,budget)
        for got,(trace,local) in zip(r['runs'],expected):
            assert got['index_trace']==list(map(list,trace)) and got['objective_trace_fraction']==[str(scores[p]) for p in trace] and got['local_minimum_observed']==local and got['moves_used']==len(trace)-1
            assert got['point_fraction']==[str(axes[i][j]) for i,j in enumerate(trace[-1])] and got['objective_fraction']==str(scores[trace[-1]])
        assert r['winner_index']==min(range(3),key=lambda i:(scores[expected[i][0][-1]],expected[i][0][-1],i))


def test_valid_caps_and_numeric_boundaries():
    for d in (1,3,4):
        for n in (1,6,7):assert explore([list(range(n))]*d,[0]*d,0,[[0]*d]*20,100)['grid_vertex_count']==n**d
    for v in (-10,10,-10.,10.):explore([[v]],[v],v,[[0]],1)
    for steps in (1,99,100):explore([[0]],[0],0,[[0]],steps)


def test_precise_staged_refusals_and_hugeints():
    for axes in (None,(),[],True,[[0]]*5):
        with pytest.raises(ValueError,match='^1..4 landscape axes before scan$'):explore(axes,[0],0,[[0]],1)
    for row in (None,(),[],True,list(range(8))):
        with pytest.raises(ValueError,match='^1..7 grid values per axis before scan$'):explore([row],[0],0,[[0]],1)
    for row in ([0,0],[1,0]):
        with pytest.raises(ValueError,match='^strict ascending grid values$'):explore([row],[0],0,[[0]],1)
    for v in (True,None,'1',-10.01,10.01,10**400,-10**400,float('inf'),float('nan')):
        for a in ([[[v]],[0],0,[[0]],1],[[[0]],[v],0,[[0]],1],[[[0]],[0],v,[[0]],1]):
            with pytest.raises(ValueError,match='^strict finite landscape number -10..10$'):explore(*a)
    for b in (None,(),[],True,[0,0]):
        with pytest.raises(ValueError,match='^one linear coefficient per axis$'):explore([[0]],b,0,[[0]],1)
    for starts in (None,(),[],True,[[0]]*21):
        with pytest.raises(ValueError,match='^1..20 starts before scan$'):explore([[0]],[0],0,starts,1)
    for row in (None,(),[],True,[0,0]):
        with pytest.raises(ValueError,match='^one strict grid index per axis$'):explore([[0]],[0],0,[row],1)
    for v in (True,None,'0',0.,-1,1,10**400):
        with pytest.raises(ValueError,match='^strict grid index in axis bounds$'):explore([[0]],[0],0,[[v]],1)
    for steps in (True,None,1.,0,101,10**400):
        with pytest.raises(ValueError,match='^strict landscape budget 1..100$'):explore([[0]],[0],0,[[0]],steps)


def test_mixed_valid_invalid_multiaxis_index_refused():
    for row in ([0,True],[0,-1],[0,1],[True,0],[-1,0],[1,0]):
        with pytest.raises(ValueError,match='^strict grid index in axis bounds$'):explore([[0],[0]],[0,0],0,[row],1)
