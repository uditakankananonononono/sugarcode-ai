from fractions import Fraction as F
import copy
import pytest
from sugarcode.extra_doc.cutting_exact240 import solve


def test_literal_separating_cut_bound_refinement_and_nomutation():
    a=[[[1,0],[-1,0]],[ -2,2],40];before=copy.deepcopy(a);r=solve(*a)
    assert r['trace']==[dict(active_plane_indices=[0],point_fraction='-2',lower_bound_fraction='-2',objective_fraction='2',gap_fraction='4',separating_plane_index=1),dict(active_plane_indices=[0,1],point_fraction='0',lower_bound_fraction='0',objective_fraction='0',gap_fraction='0',separating_plane_index=0)]
    assert r['point_fraction']=='0' and r['objective_fraction']=='0' and r['converged_exact_in_supplied_model'] and r['iterations_used']==2 and r['external_effects']==[] and a==before
    r=solve(*a[:2],1);assert not r['converged_exact_in_supplied_model'] and r['gap_fraction']=='4'


def test_500_independent_allplane_pair_intersection_lp_references():
    from random import Random
    from itertools import combinations
    rng=Random(240)
    for _ in range(500):
        planes=[[rng.randrange(-8,9),rng.randrange(-8,9)] for i in range(rng.randrange(1,20))];lo=rng.randrange(-8,1);hi=rng.randrange(0,9);points={F(lo),F(hi)}
        for (a,b),(c,d) in combinations(planes,2):
            if a!=c:
                v=F(d-b,a-c)
                if lo<=v<=hi:points.add(v)
        scores={x:max(a*x+b for a,b in planes) for x in points};x=min(scores,key=lambda x:(scores[x],x));r=solve(planes,[lo,hi],40)
        assert F(r['point_fraction'])==x and F(r['objective_fraction'])==scores[x] and r['converged_exact_in_supplied_model'] and r['gap_fraction']=='0'
        lower=[F(s['lower_bound_fraction']) for s in r['trace']];assert all(v>=u for u,v in zip(lower,lower[1:]))
        for s in r['trace']:
            p=F(s['point_fraction']);active=s['active_plane_indices'];assert F(s['lower_bound_fraction'])==max(planes[i][0]*p+planes[i][1] for i in active)
            assert s['separating_plane_index']==max(range(len(planes)),key=lambda i:(planes[i][0]*p+planes[i][1],-i))
            assert F(s['objective_fraction'])-F(s['lower_bound_fraction'])==F(s['gap_fraction'])


def test_caps_equal_bounds_and_signed_endpoints():
    for n in (1,39,40):solve([[1,0]]*n,[-1000,1000],40)
    for v in (-1000,1000,-1000.,1000.):solve([[v,v]],[v,v],1)
    for k in (1,39,40):solve([[0,0]],[0,0],k)


def test_precise_refusals_types_shapes_numeric_hugeints():
    for p in (None,(),[],True,[[0,0]]*41):
        with pytest.raises(ValueError,match='^1..40 affine planes before scan$'):solve(p,[0,1],1)
    for b in (None,(),[],True,[0],[0]*3):
        with pytest.raises(ValueError,match='^two cutting interval bounds$'):solve([[0,0]],b,1)
    for p in (None,(),[],True,[0],[0]*3):
        with pytest.raises(ValueError,match='^affine plane slope and intercept pair$'):solve([p],[0,1],1)
    with pytest.raises(ValueError,match='^ordered cutting bounds$'):solve([[0,0]],[1,0],1)
    for v in (True,None,'1',-1000.01,1000.01,10**400,-10**400,float('nan'),float('inf')):
        for a in ([[[v,0]],[0,1],1],[[[0,v]],[0,1],1],[[[0,0]],[v,1],1],[[[0,0]],[0,v],1]):
            with pytest.raises(ValueError,match='^strict finite cutting number -1000..1000$'):solve(*a)
    for k in (True,None,1.,0,41,10**400):
        with pytest.raises(ValueError,match='^strict cutting iterations 1..40$'):solve([[0,0]],[0,1],k)
