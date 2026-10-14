import copy
import pytest
from sugarcode.extra_doc.quadratic_descent228 import descend


def args():return [[[4,1],[1,2]],[-1,2],[2,-1],100,1e-8]


def test_independent_hand_steepest_direction_exact_line_step_and_linear_solve():
    a=args();before=copy.deepcopy(a);r=descend(*a)
    # initial gradient [6,2], gAg=176, alpha=40/176=5/22
    assert r['step_sizes'][0]==pytest.approx(5/22)
    assert r['point_history'][1]==pytest.approx([7/11,-16/11])
    # A^-1 (-b): determinant7 -> [4/7,-9/7]
    assert r['point']==pytest.approx([4/7,-9/7],abs=1e-8)
    assert r['converged'] and r['gradient_norm']<=1e-8
    assert all(later<=earlier+1e-12 for earlier,later in zip(r['objective_history'],r['objective_history'][1:]))
    assert r['objective']==pytest.approx(-11/7) and r['objective_history'][0]==3
    assert a==before and not r['global_optimum_claimed'] and r['external_effects']==[]


def test_stationary_initial_zero_iterations_used_and_budget_exhaustion():
    r=descend([[2]],[-4],[2],1,1e-10)
    assert r['point']==[2] and r['iterations_used']==0 and r['step_sizes']==[] and r['objective_history']==[-4] and r['converged']
    a=args();a[3]=1;r=descend(*a)
    assert r['iterations_used']==1 and not r['converged'] and len(r['point_history'])==2
    assert r['method']=='steepest_descent_exact_quadratic_line_search' and r['objective_definition']=='0.5*x^T*A*x + b^T*x'


def test_250_independent_decimal_first_step_and_closed_form_optimum():
    from random import Random
    from decimal import Decimal
    rng=Random(228)
    for _ in range(250):
        p=rng.randint(2,12);q=rng.randint(2,12);c=rng.choice([-1,0,1]);b=[rng.randint(-4,4),rng.randint(-4,4)];x=[rng.randint(-4,4),rng.randint(-4,4)]
        g0=Decimal(p*x[0]+c*x[1]+b[0]);g1=Decimal(c*x[0]+q*x[1]+b[1]);n=g0*g0+g1*g1
        r=descend([[p,c],[c,q]],b,x,100,1e-7)
        if n:
            alpha=n/(Decimal(p)*g0*g0+2*Decimal(c)*g0*g1+Decimal(q)*g1*g1)
            assert r['step_sizes'][0]==pytest.approx(float(alpha),rel=1e-12)
            assert r['point_history'][1]==pytest.approx([float(Decimal(x[0])-alpha*g0),float(Decimal(x[1])-alpha*g1)],abs=1e-12)
        det=p*q-c*c;expected=[(-q*b[0]+c*b[1])/det,(c*b[0]-p*b[1])/det]
        assert r['point']==pytest.approx(expected,abs=1e-7)


def test_full_dimension_numeric_iterations_tolerance_endpoints():
    for d in (1,7,8):
        a=[[1 if i==j else 0 for j in range(d)] for i in range(d)]
        assert descend(a,[0]*d,[1000]*d,100,1)['point']==[0]*d
    for v in (-1000,1000,-1000.0,1000.0):
        descend([[1000]],[v],[v],1,1e-10)
    for n in (1,99,100):descend([[1]],[0],[0],n,1)
    for tol in (1e-10,1):descend([[1]],[0],[0],1,tol)
    assert descend([[.000001]],[0],[0],1,1)['converged']


def test_strict_refusals_with_precise_stage_messages():
    for n in (True,1.0,0,101,None):
        a=args();a[3]=n
        with pytest.raises(ValueError,match='^strict iteration count 1..100$'):descend(*a)
    for tol in (True,'1',None,0.000000000099,1.01,float('nan'),float('inf')):
        a=args();a[4]=tol
        with pytest.raises(ValueError,match='^strict finite tolerance 1e-10..1$'):descend(*a)
    for init in ([],[0]*9,None,(),True):
        a=args();a[2]=init
        with pytest.raises(ValueError,match='^1..8 initial coordinates before scan$'):descend(*a)
    for v in (True,'1',None,-1000.01,1000.01,float('nan'),float('inf')):
        for slot in (0,1):
            for index in (1,2):
                a=args();a[index][slot]=v
                with pytest.raises(ValueError,match='^strict finite quadratic number within -1000..1000$'):descend(*a)
            a=args();a[0][0][slot]=v
            with pytest.raises(ValueError,match='^strict finite quadratic number within -1000..1000$'):descend(*a)
    for bad in (None,(),[],[1],[1,2,3]):
        a=args();a[1]=bad
        with pytest.raises(ValueError,match='^one coordinate per dimension$'):descend(*a)
        a=args();a[0][0]=bad
        with pytest.raises(ValueError,match='^one coordinate per dimension$'):descend(*a)
    for bad in (None,(),[],[[1]]):
        a=args();a[0]=bad
        with pytest.raises(ValueError,match='^square matrix dimension$'):descend(*a)
    with pytest.raises(ValueError,match='^symmetric quadratic matrix$'):descend([[2,0],[1,2]],[0,0],[0,0],1,1)
    for a in ([[0]],[[.00000099]],[[-1]],[[1,2],[2,1]],[[1,1],[1,1]]):
        d=len(a)
        with pytest.raises(ValueError,match='^positive definite matrix with LDL pivots at least 1e-6$'):descend(a,[0]*d,[0]*d,1,1)


def test_gradient_norm_equals_tolerance_is_already_converged():
    r=descend([[1]],[0],[1],1,1)
    assert r['iterations_used']==0 and r['point']==[1] and r['gradient_norm']==1 and r['converged']


def test_defensive_numerical_faults_at_curvature_and_first_iterate(monkeypatch):
    import sugarcode.extra_doc.quadratic_descent228 as m
    original=m.math.isfinite
    # Validation calls: tolerance, 2 initial, 2 linear, 4 matrix; then curvature.
    for fail_at,message in ((10,'positive finite numerical curvature required'),(11,'finite numerical iterate required')):
        counter=[0]
        def finite(v):
            counter[0]+=1
            return False if counter[0]==fail_at else original(v)
        with monkeypatch.context() as patch:
            patch.setattr(m.math,'isfinite',finite)
            with pytest.raises(ValueError,match='^'+message+'$'):descend(*args())


def test_three_axis_ldl_indefinite_and_near_pivot_boundary_refused():
    for matrix in ([[1,0,2],[0,1,2],[2,2,1]],[[2,1,1],[1,2,2],[1,2,2]],[[.0000009999995]]):
        d=len(matrix)
        with pytest.raises(ValueError,match='^positive definite matrix with LDL pivots at least 1e-6$'):descend(matrix,[0]*d,[0]*d,1,1)


def test_zero_curvature_fault_refused(monkeypatch):
    import sugarcode.extra_doc.quadratic_descent228 as m
    original=m.math.fsum;counter=[0]
    def total(values):
        counter[0]+=1
        return 0.0 if counter[0]==12 else original(values)
    monkeypatch.setattr(m.math,'fsum',total)
    with pytest.raises(ValueError,match='^positive finite numerical curvature required$'):descend(*args())


def test_nonzero_second_column_schur_complement_accepted():
    r=descend([[7,7,5],[7,8,5],[5,5,5]],[0,0,0],[0,0,0],1,1)
    assert r['converged'] and r['point']==[0,0,0]


@pytest.mark.parametrize('huge',[10**400,-10**400])
def test_huge_integers_refused_before_any_float_operation(huge):
    a=args();a[4]=huge
    with pytest.raises(ValueError,match='^strict finite tolerance 1e-10..1$'):descend(*a)
    for index in (1,2):
        for j in (0,1):
            a=args();a[index][j]=huge
            with pytest.raises(ValueError,match='^strict finite quadratic number within -1000..1000$'):descend(*a)
    for i in (0,1):
        for j in (0,1):
            a=args();a[0][i][j]=huge
            with pytest.raises(ValueError,match='^strict finite quadratic number within -1000..1000$'):descend(*a)
