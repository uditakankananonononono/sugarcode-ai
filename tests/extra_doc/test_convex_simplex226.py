import copy
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.convex_simplex226 import solve


def test_hand_interior_boundary_kkt_and_no_mutation():
    a=[[2,4,1],[2,4,-3],2];before=copy.deepcopy(a);r=solve(*a)
    assert r['point_fraction']==['1','1','0'] and r['objective_fraction']=='-3' and r['equality_multiplier_fraction']=='0'
    assert r['nonnegative_multipliers_fraction']==['0','0','3'] and r['active_indices']==[0,1] and r['sum_fraction']=='2' and r['kkt_verified_in_supplied_model'] and r['external_effects']==[] and a==before
    assert r['scope']=='unique exact convex optimum in supplied nonnegative sum-equality quadratic'


def test_500_independent_sorted_breakpoint_waterfill_oracles():
    from random import Random
    rng=Random(226)
    for _ in range(500):
        n=rng.randrange(1,9);a=[rng.randrange(1,10) for i in range(n)];b=[rng.randrange(-6,7) for i in range(n)];t=rng.randrange(1,10);order=sorted(range(n),key=lambda i:-b[i]);active=[];lam=None
        for i in order:
            active.append(i);lam=(sum(F(b[j],a[j]) for j in active)-t)/sum(F(1,a[j]) for j in active)
            remainder=[k for k in order if k not in active]
            if not remainder or lam>=b[remainder[0]]:break
        x=[max(F(0),(b[i]-lam)/a[i]) for i in range(n)];r=solve(a,b,t)
        assert list(map(F,r['point_fraction']))==x and F(r['equality_multiplier_fraction'])==lam and r['kkt_verified_in_supplied_model']
        assert F(r['objective_fraction'])==sum(F(a[i],2)*x[i]**2-b[i]*x[i] for i in range(n))
        assert list(map(F,r['nonnegative_multipliers_fraction']))==[a[i]*x[i]-b[i]+lam for i in range(n)]


def test_caps_active_set_counts_equal_curvature_and_numeric_boundaries():
    for n in (1,7,8):
        r=solve([1]*n,[0]*n,n);assert r['point_fraction']==['1']*n and r['active_sets_checked']==2**n-1
    for v in (-1000,1000,-1000.0,1000.0):solve([1000],[v],1000)
    solve([.000001],[0],.000001)
    r=solve([1,1],[1,0],1);assert r['point_fraction']==['1','0'] and r['active_indices']==[0]


def test_all_caps_shapes_numeric_hugeints_and_nonbool_refusals():
    for a in (None,(),[],True,[1]*9):
        with pytest.raises(ValueError,match='^1..8 convex dimensions before scan$'):solve(a,[0],1)
    for b in (None,(),[],True,[0],[0]*3):
        with pytest.raises(ValueError,match='^one linear value per convex dimension$'):solve([1,1],b,1)
    for bad in (True,None,'1',-1000.01,1000.01,10**400,-10**400,float('nan'),float('inf')):
        for slot in (0,1,2):
            a=[[1,1],[0,0],1]
            if slot==2:a[2]=bad
            else:a[slot][1]=bad
            with pytest.raises(ValueError,match='^strict finite bounded convex number$'):solve(*a)
    for bad in (0,.00000099,-1):
        with pytest.raises(ValueError,match='^strict finite bounded convex number$'):solve([bad],[0],1)
        with pytest.raises(ValueError,match='^strict finite bounded convex number$'):solve([1],[0],bad)
