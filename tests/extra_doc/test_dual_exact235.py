import pytest
from sugarcode.extra_doc.dual_exact235 import solve


def test_independent_weighted_signed_hand_kkt_duality_and_unused_block():
    r=solve([2,4,1],[2,-4,3],[1,-2,0],5)
    # unconstrained [1,-1,3],weighted sum3;curvature1/2+1=3/2,lambda=-4/3
    assert r['point_fraction']==['5/3','-5/3','3'] and r['multiplier_fraction']=='-4/3'
    assert r['dual_curvature_fraction']=='3/2' and r['coupling_residual_fraction']=='0' and r['duality_gap_fraction']=='0'
    assert r['primal_objective_fraction']==r['dual_bound_fraction']


def test_500_independent_equality_elimination_two_block_oracles():
    from fractions import Fraction as F
    from random import Random
    rng=Random(235)
    for _ in range(500):
        a=[rng.randrange(1,10),rng.randrange(1,10)];b=[rng.randrange(-5,6),rng.randrange(-5,6)];c=[rng.choice([-3,-2,-1,1,2,3]),rng.choice([-3,-2,-1,1,2,3])];total=rng.randrange(-5,6)
        # Eliminate x1=(total-c0*x0)/c1; derivative of resulting scalar quadratic.
        h=F(a[0])+F(a[1]*c[0]*c[0],c[1]*c[1]);rhs=F(b[0])+F(a[1]*c[0]*total,c[1]*c[1])-F(b[1]*c[0],c[1])
        x0=rhs/h;x1=(F(total)-c[0]*x0)/c[1];r=solve(a,b,c,total)
        assert list(map(F,r['point_fraction']))==[x0,x1]
        objective=F(a[0])*x0*x0/2+F(a[1])*x1*x1/2-b[0]*x0-b[1]*x1
        assert F(r['primal_objective_fraction'])==objective==F(r['dual_bound_fraction'])
        assert r['duality_gap_fraction']=='0' and r['coupling_residual_fraction']=='0'


def test_full_cap_boundaries_zero_coupling_and_input_preservation():
    import copy
    for n in (1,19,20):
        a=[[1]*n,[0]*n,[1]*n,0];before=copy.deepcopy(a)
        assert solve(*a)['point_fraction']==['0']*n and a==before
    for v in (-1000,1000,-1000.0,1000.0):solve([1000],[v],[v],v)
    solve([.000001],[0],[1],0)
    r=solve([1,1],[1,2],[0,1],0)
    assert r['point_fraction']==['1','0'] and r['external_effects']==[]


def test_every_staged_type_numeric_and_schema_refusal():
    for a in (None,(),[],True,[1]*21):
        with pytest.raises(ValueError,match='^1..20 separable blocks before scan$'):solve(a,[0],[1],0)
    for index in (1,2):
        for vector in (None,(),[],[1],[1]*3):
            a=[[1,1],[0,0],[1,1],0];a[index]=vector
            with pytest.raises(ValueError,match='^one value per separable block$'):solve(*a)
    for index in (0,1,2,3):
        for bad in (True,'1',None,-1000.01,1000.01,10**400,-10**400,float('nan'),float('inf')):
            for j in (0,1):
                a=[[1,1],[0,0],[1,1],0]
                if index==3:a[3]=bad
                else:a[index][j]=bad
                with pytest.raises(ValueError,match='^strict finite bounded decomposition number$'):solve(*a)
    for bad in (0,-1,.00000099):
        with pytest.raises(ValueError,match='^strict finite bounded decomposition number$'):solve([bad],[0],[1],0)
    with pytest.raises(ValueError,match='^at least one nonzero coupling coefficient$'):solve([1,1],[0,0],[0,0],0)
