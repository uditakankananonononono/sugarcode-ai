import copy
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.coordinate_exact237 import solve


def args():return [[[4,1],[1,2]],[1,-2],[2,-1],30,1e-9]


def test_asymmetric_hand_one_coordinate_at_a_time_and_objective():
    a=args();a[3]=1;before=copy.deepcopy(a);r=solve(*a)
    assert r['trace'][0]['point_before_fraction']==['2','-1']
    assert r['trace'][0]['point_after_fraction']==['1/2','-1']
    assert r['trace'][1]['point_before_fraction']==['1/2','-1'] and r['trace'][1]['point_after_fraction']==['1/2','-5/4']
    assert r['objective_history_fraction']==['3','-3/2','-25/16'] and r['gradient_fraction']==['-1/4','0']
    assert r['point_fraction']==['1/2','-5/4'] and r['gradient_infinity_fraction']=='1/4' and not r['converged_gradient_tolerance']
    assert [q['coordinate'] for q in r['trace']]==[0,1] and [q['sweep'] for q in r['trace']]==[1,1]
    assert a==before and r['external_effects']==[] and not r['global_optimum_claimed']


def test_350_independent_scalar_slice_exact_update_oracles():
    from random import Random
    rng=Random(237)
    for _ in range(350):
        a=rng.randrange(2,9);d=rng.randrange(2,9);c=rng.choice([-1,0,1]);b=[rng.randrange(-4,5),rng.randrange(-4,5)];x=[F(rng.randrange(-4,5)),F(rng.randrange(-4,5))];r=solve([[a,c],[c,d]],b,list(map(int,x)),4,1e-9)
        for t,step in enumerate(r['trace']):
            j=t%2;previous=x[:]
            # Scalar slice derivative: curvature*x + coupling*fixed-other - linear.
            if j==0:x[0]=F(b[0]-c*x[1],a)
            else:x[1]=F(b[1]-c*x[0],d)
            assert list(map(F,step['point_before_fraction']))==previous and list(map(F,step['point_after_fraction']))==x
            val=F(a,2)*x[0]**2+c*x[0]*x[1]+F(d,2)*x[1]**2-b[0]*x[0]-b[1]*x[1]
            assert F(step['objective_fraction'])==val
        assert all(F(v)<=F(u) for u,v in zip(r['objective_history_fraction'],r['objective_history_fraction'][1:]))
        assert list(map(F,r['gradient_fraction']))==[a*x[0]+c*x[1]-b[0],c*x[0]+d*x[1]-b[1]]


def test_full_caps_pivot_boundary_convergence_and_tolerance_equality():
    for d in (1,7,8):
        a=[[1 if i==j else 0 for j in range(d)] for i in range(d)]
        for n in (1,29,30):assert solve(a,[0]*d,[1000]*d,n,1)['point_fraction']==['0']*d
    for v in (-1000,1000,-1000.0,1000.0):solve([[1000]],[v],[v],1,1)
    solve([[.000001]],[0],[0],1,1e-9)
    r=solve([[4,1],[1,2]],[1,-2],[2,-1],1,.25)
    assert r['converged_gradient_tolerance'] and r['sweeps_used']==1
    r=solve(*args());assert list(map(float,map(F,r['point_fraction'])))==pytest.approx([4/7,-9/7],abs=1e-8)
    assert r['method']=='exact cyclic one-coordinate quadratic minimization' and r['objective_definition']=='0.5*x^T*A*x - b^T*x'


def test_caps_type_shapes_symmetry_spd_and_huge_integer_refusals():
    for n in (True,1.0,0,31,None):
        a=args();a[3]=n
        with pytest.raises(ValueError,match='^strict coordinate sweeps 1..30$'):solve(*a)
    for init in (True,None,(),[],[0]*9):
        a=args();a[2]=init
        with pytest.raises(ValueError,match='^1..8 coordinate dimensions before scan$'):solve(*a)
    for bad in (None,(),[],[0],[0]*3):
        a=args();a[1]=bad
        with pytest.raises(ValueError,match='^one value per coordinate dimension$'):solve(*a)
        a=args();a[0][0]=bad
        with pytest.raises(ValueError,match='^one value per coordinate dimension$'):solve(*a)
    for bad in (None,(),[],[[1]]):
        a=args();a[0]=bad
        with pytest.raises(ValueError,match='^square coordinate matrix dimension$'):solve(*a)
    for bad in (True,None,'1',-1000.01,1000.01,10**400,-10**400,float('nan'),float('inf')):
        for index in (1,2):
            for j in (0,1):
                a=args();a[index][j]=bad
                with pytest.raises(ValueError,match='^strict finite bounded coordinate number$'):solve(*a)
        for i in (0,1):
            for j in (0,1):
                a=args();a[0][i][j]=bad
                with pytest.raises(ValueError,match='^strict finite bounded coordinate number$'):solve(*a)
        a=args();a[4]=bad
        with pytest.raises(ValueError,match='^strict finite bounded coordinate number$'):solve(*a)
    for bad in (0,.00000000099,1.01):
        a=args();a[4]=bad
        with pytest.raises(ValueError,match='^strict finite bounded coordinate number$'):solve(*a)
    with pytest.raises(ValueError,match='^symmetric coordinate matrix$'):solve([[2,1],[0,2]],[0,0],[0,0],1,1)
    for matrix in ([[0]],[[-1]],[[.0000009999995]],[[1,2],[2,1]],[[1,1],[1,1]],[[2,1,1],[1,2,2],[1,2,2]]):
        n=len(matrix)
        with pytest.raises(ValueError,match='^positive definite coordinate matrix pivots >=1e-6$'):solve(matrix,[0]*n,[0]*n,1,1)
    assert solve([[7,7,5],[7,8,5],[5,5,5]],[0]*3,[0]*3,1,1)['converged_gradient_tolerance']
