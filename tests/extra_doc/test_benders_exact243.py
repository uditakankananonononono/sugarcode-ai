import copy
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.benders_exact243 import solve


def test_hand_master_recourse_dual_cut_and_nomutation():
    a=[[[0,0],[2,1],[4,3]],[3],[2],80];before=copy.deepcopy(a);r=solve(*a)
    assert r['trace'][0]==dict(option_index=0,lower_bound_fraction='0',incumbent_objective_fraction='6',incumbent_index=0,recourse_fraction='6',shortages_fraction=['3'],dual_fraction=['2'],cut_intercept_fraction='6',cut_slope_fraction='-2',gap_fraction='6',cuts_used=1)
    assert r['selected_index']==1 and r['objective_fraction']=='3' and r['lower_bound_fraction']=='3' and r['gap_fraction']=='0' and r['converged_exact_in_supplied_menu'] and r['external_effects']==[] and a==before
    assert not solve(*a[:3],1)['converged_exact_in_supplied_menu']


def test_500_independent_fullmenu_recourse_references_and_cut_validity():
    from random import Random
    rng=Random(243)
    for _ in range(500):
        menu=[[rng.randrange(0,15),rng.randrange(-5,15)] for i in range(rng.randrange(1,20))];d=[rng.randrange(0,15) for i in range(rng.randrange(1,10))];p=[rng.randrange(0,8) for i in d];costs=[F(c)+sum(F(q)*(v-x) for v,q in zip(d,p) if v>x) for x,c in menu];best=min(costs);r=solve(menu,d,p,80)
        assert F(r['objective_fraction'])==best and costs[r['selected_index']]==best and r['converged_exact_in_supplied_menu'] and r['gap_fraction']=='0'
        lows=[F(s['lower_bound_fraction']) for s in r['trace']];assert all(v>=u for u,v in zip(lows,lows[1:]))
        for s in r['trace']:
            x,c=menu[s['option_index']];shortages=[max(v-x,0) for v in d];assert list(map(F,s['shortages_fraction']))==shortages and F(s['recourse_fraction'])==sum(v*q for v,q in zip(shortages,p))
            dual=list(map(F,s['dual_fraction']));assert dual==[F(q if v>x else 0) for v,q in zip(d,p)]
            alpha=F(s['cut_intercept_fraction']);beta=F(s['cut_slope_fraction']);assert alpha+beta*x==F(s['recourse_fraction'])
            assert all(alpha+beta*y<=sum(F(q)*max(v-y,0) for v,q in zip(d,p)) for y,c in menu)
            assert F(s['lower_bound_fraction'])<=best<=F(s['incumbent_objective_fraction'])


def test_caps_endpoints_and_zero_recourse():
    for n in (1,79,80):assert solve([[0,0]]*n,[0]*20,[1000]*20,80)['selected_index']==0
    for v in (1000,1000.):solve([[v,-v],[0,v]],[v],[v],80)
    for k in (1,79,80):solve([[0,0]],[0],[0],k)
    assert solve([[1,0]],[1],[1],1)['trace'][0]['dual_fraction']==['0']


def test_strict_shapes_numeric_hugeint_and_caps_refusals():
    for menu in (None,(),[],True,[[0,0]]*81):
        with pytest.raises(ValueError,match='^1..80 Benders options before scan$'):solve(menu,[0],[0],1)
    for d in (None,(),[],True,[0]*21):
        with pytest.raises(ValueError,match='^1..20 Benders recourse demands before scan$'):solve([[0,0]],d,[0],1)
    for row in (None,(),[],True,[0],[0]*3):
        with pytest.raises(ValueError,match='^Benders capacity and fixed cost pair$'):solve([row],[0],[0],1)
    for p in (None,(),[],True,[0,0]):
        with pytest.raises(ValueError,match='^one penalty per Benders demand$'):solve([[0,0]],[0],p,1)
    for bad in (True,None,'1',-1000.01,1000.01,10**400,-10**400,float('nan'),float('inf')):
        for a in (([[bad,0]],[0],[0],1),([[0,bad]],[0],[0],1),([[0,0]],[bad],[0],1),([[0,0]],[0],[bad],1)):
            with pytest.raises(ValueError,match='^strict finite bounded Benders number$'):solve(*a)
    for a in (([[-.01,0]],[0],[0],1),([[0,0]],[-.01],[0],1),([[0,0]],[0],[-.01],1)):
        with pytest.raises(ValueError,match='^strict finite bounded Benders number$'):solve(*a)
    for k in (True,None,1.,0,81,10**400):
        with pytest.raises(ValueError,match='^strict Benders iterations 1..80$'):solve([[0,0]],[0],[0],k)
