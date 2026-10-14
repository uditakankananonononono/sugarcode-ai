import copy
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.column_exact242 import solve


def test_hand_restricted_master_negative_reduced_cost_and_generated_column():
    a=[[[0,2],[2,2],[1,0]],1,80];before=copy.deepcopy(a);r=solve(*a)
    assert r['trace'][0]==dict(active_column_indices=[0,1],basis_indices=[0,1],weights_fraction=['1/2','1/2'],restricted_objective_fraction='2',dual_intercept_fraction='2',dual_slope_fraction='0',pricing_column_index=2,reduced_cost_fraction='-2')
    assert r['basis_indices']==[0,2] and r['weights_fraction']==['0','1'] and r['objective_fraction']=='0' and r['converged_exact_in_supplied_menu'] and r['iterations_used']==2 and r['external_effects']==[] and a==before
    assert not solve(*a[:2],1)['converged_exact_in_supplied_menu']


def test_400_independent_allcolumn_primal_mixture_lp_oracles():
    from itertools import combinations
    from random import Random
    rng=Random(242)
    for _ in range(400):
        columns=[[-5,rng.randrange(-8,9)],[5,rng.randrange(-8,9)]]+[[rng.randrange(-5,6),rng.randrange(-8,9)] for i in range(rng.randrange(0,18))];t=rng.randrange(-5,6);options=[]
        for q,c in columns:
            if q==t:options.append(F(c))
        for (q,c),(r,d) in combinations(columns,2):
            if q!=r and min(q,r)<=t<=max(q,r):w=F(r-t,r-q);options.append(w*c+(1-w)*d)
        best=min(options);r=solve(columns,t,80);assert F(r['objective_fraction'])==best and r['converged_exact_in_supplied_menu']
        objectives=[F(s['restricted_objective_fraction']) for s in r['trace']];assert all(v<=u for u,v in zip(objectives,objectives[1:]))
        for s in r['trace']:
            basis=s['basis_indices'];weights=list(map(F,s['weights_fraction']));alpha=F(s['dual_intercept_fraction']);beta=F(s['dual_slope_fraction']);active=s['active_column_indices'];cost=F(s['restricted_objective_fraction'])
            assert sum(weights)==1 and all(w>=0 for w in weights) and sum(w*columns[i][0] for i,w in zip(basis,weights))==t and sum(w*columns[i][1] for i,w in zip(basis,weights))==cost==alpha+beta*t
            assert all(alpha+beta*columns[i][0]<=columns[i][1] for i in active)
            pricing=[F(c)-alpha-beta*q for q,c in columns];assert s['pricing_column_index']==min(range(len(columns)),key=lambda i:(pricing[i],i)) and F(s['reduced_cost_fraction'])==min(pricing)


def test_caps_numeric_endpoints_equal_target_and_duplicates():
    for n in (2,79,80):solve([[-1000,-1000],[1000,1000]]+[[0,0]]*(n-2),0,80)
    for v in (-1000,1000,-1000.,1000.):solve([[-1000,v],[1000,v]],v,1)
    for k in (1,79,80):solve([[0,0],[1,1]],0,k)
    assert solve([[0,2],[1,1],[0,0]],0,80)['objective_fraction']=='0'


def test_precise_shapes_bounds_hugeints_and_hull_refusals():
    for columns in (None,(),[],True,[[0,0]],[[0,0]]*81):
        with pytest.raises(ValueError,match='^2..80 columns before scan$'):solve(columns,0,1)
    for row in (None,(),[],True,[0],[0]*3):
        with pytest.raises(ValueError,match='^column coordinate and cost pair$'):solve([[0,0],row],0,1)
    for bad in (True,None,'1',-1000.01,1000.01,10**400,-10**400,float('nan'),float('inf')):
        for a in (([[0,0],[bad,1]],0,1),([[0,0],[1,bad]],0,1),([[0,0],[1,1]],bad,1)):
            with pytest.raises(ValueError,match='^strict finite column number -1000..1000$'):solve(*a)
    for columns,t in (([[0,0],[0,1]],0),([[0,0],[1,1]],-1),([[0,0],[1,1]],2)):
        with pytest.raises(ValueError,match='^target in nondegenerate column coordinate hull$'):solve(columns,t,1)
    for k in (True,None,1.,0,81,10**400):
        with pytest.raises(ValueError,match='^strict column iterations 1..80$'):solve([[0,0],[1,1]],0,k)


@pytest.mark.parametrize('columns,target,basis,weights',[
    ([[-3,-1],[-4,2],[-4,-1]],-4,[0,2],['0','1']),
    ([[2,2],[-3,-1],[-3,4]],2,[0],['1']),
    ([[4,3],[3,4],[-1,-2],[4,3],[-2,-3],[3,0]],-2,[4],['1']),
    ([[2,1],[4,-2],[0,-2],[-1,3],[-3,4],[0,4],[1,0]],0,[1,2],['0','1']),
])
def test_exact_degenerate_basis_weight_tie_witnesses(columns,target,basis,weights):
    r=solve(columns,target,80)
    assert r['basis_indices']==basis and r['weights_fraction']==weights
