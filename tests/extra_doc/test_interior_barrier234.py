import copy
import math
import pytest
from sugarcode.extra_doc.interior_barrier234 import optimize


def args():return [[2,4],[-1,2],[-2,-2],[3,3],[0,0],[1,.1,.01],10]


def test_hand_gradient_hessian_direction_feasibility_and_nomutation():
    a=args();before=copy.deepcopy(a);r=optimize(*a);s=r['steps'][0]
    assert s['gradient']==pytest.approx([-7/6,11/6]) and s['hessian_diagonal']==pytest.approx([85/36,157/36]) and s['direction']==pytest.approx([42/85,-66/157]) and s['step_size']==1
    assert r['strict_interior'] and all(v>0 for v in r['slacks_lower']+r['slacks_upper']) and not r['global_optimum_claimed'] and r['external_effects']==[] and a==before
    assert r['point']==pytest.approx([.5,-.5],abs=.01)
    assert all(s['barrier_objective_after']<=s['barrier_objective_before'] for s in r['steps'])


def test_250_independent_decimal_first_step_barrier_derivatives():
    from decimal import Decimal as D,localcontext
    from random import Random
    rng=Random(234)
    with localcontext() as ctx:
        ctx.prec=60
        for _ in range(250):
            n=rng.randrange(1,9);a=[rng.randrange(1,8) for i in range(n)];b=[rng.randrange(-3,4) for i in range(n)];x=[rng.randrange(-1,2) for i in range(n)];mu=D('.5');g=[];h=[];p=[]
            for q,c,z in zip(a,b,x):
                z=D(z);g.append(D(q)*z+c-mu/(z+3)+mu/(4-z));h.append(D(q)+mu/(z+3)**2+mu/(4-z)**2);p.append(-g[-1]/h[-1])
            r=optimize(a,b,[-3]*n,[4]*n,x,[.5],1)
            if not r['steps']:assert all(abs(v)<=D('1e-8') for v in g);continue
            s=r['steps'][0]
            for key,expected in [('gradient',g),('hessian_diagonal',h),('direction',p)]:assert s[key]==pytest.approx(list(map(float,expected)),abs=1e-12)
            assert s['point']==pytest.approx([float(D(z)+D(str(s['step_size']))*v) for z,v in zip(x,p)],abs=1e-12)
            assert s['barrier_objective_before']==pytest.approx(sum(.5*q*z*z+c*z for q,c,z in zip(a,b,x))-.5*sum(math.log(z+3)+math.log(4-z) for z in x),abs=1e-12)
            assert r['slacks_lower']==pytest.approx([v+3 for v in r['point']]) and r['slacks_upper']==pytest.approx([4-v for v in r['point']])


def test_caps_boundary_values_stationary_and_constraint_limited_step():
    for n in (1,7,8):assert optimize([100]*n,[0]*n,[-100]*n,[100]*n,[0]*n,[100],20)['steps']==[]
    for v in (-100,100,-100.,100.):optimize([100],[v],[-100],[100],[0],[100],1)
    optimize([.001],[0],[0],[.001],[.0005],[.000001],1)
    for k in (1,19,20):optimize([1],[0],[-1],[1],[0],[1],k)
    for mus in ([1],[1,.9,.8,.7,.6,.5,.4,.3,.2,.1]):optimize([1],[0],[-1],[1],[0],mus,1)
    r=optimize([.001],[-100],[0],[1],[.5],[.000001],1);assert 0<r['steps'][0]['step_size']<1 and r['strict_interior']


def test_strict_staged_refusals_nonbool_hugeints():
    for initial in (None,(),[],True,[0]*9):
        a=args();a[4]=initial
        with pytest.raises(ValueError,match='^1..8 interior coordinates before scan$'):optimize(*a)
    for row in (None,(),[],True,[0],[0]*3):
        for slot in range(4):
            a=args();a[slot]=row
            with pytest.raises(ValueError,match='^one interior value per dimension$'):optimize(*a)
    for bad in (True,None,'1',-100.01,100.01,10**400,-10**400,float('nan'),float('inf')):
        for slot in range(6):
            a=args();a[slot][0]=bad
            with pytest.raises(ValueError,match='^strict finite bounded interior number$'):optimize(*a)
    for slot in (0,5):
        for v in (0,-1,.00000099):
            a=args();a[slot][0]=v
            with pytest.raises(ValueError,match='^strict finite bounded interior number$'):optimize(*a)
    for v in (-2,3,4):
        a=args();a[4][0]=v
        with pytest.raises(ValueError,match='^strict interior point with box width at least .001$'):optimize(*a)
    with pytest.raises(ValueError,match='^strict interior point with box width at least .001$'):optimize([1],[0],[0],[.00099],[.0005],[1],1)
    for barriers in (None,(),[],True,[1]*11):
        a=args();a[5]=barriers
        with pytest.raises(ValueError,match='^1..10 barriers before scan$'):optimize(*a)
    for barriers in ([1,1],[1,2]):
        a=args();a[5]=barriers
        with pytest.raises(ValueError,match='^strict decreasing positive barriers$'):optimize(*a)
    for k in (True,None,1.,0,21,10**400):
        a=args();a[6]=k
        with pytest.raises(ValueError,match='^strict interior Newton steps 1..20$'):optimize(*a)


def test_fraction_to_boundary_step_both_signs_and_nonzero_limits():
    for b in (-100,100):
        r=optimize([.001],[b],[-2],[3],[.5],[.000001],1);s=r['steps'][0];p=s['direction'][0]
        assert s['step_size']==pytest.approx(.99*(3-.5)/p if p>0 else .99*(-2-.5)/p,rel=1e-12)
        assert s['point']==pytest.approx([2.975 if p>0 else -1.975],abs=1e-12)


def test_natural_armijo_backtracking_literal_point_and_step():
    r=optimize([.0027401794949267946],[-85.97006090159817],[-48.05094725045404],[7.669396702197396],[2.5773616693397656],[96.07797947602411],1)
    s=r['steps'][0]
    assert s['step_size']==pytest.approx(.13684383086244278,rel=1e-13)
    assert s['point']==pytest.approx([5.097919010604293],abs=1e-12)
    assert s['barrier_objective_after']==pytest.approx(-910.7037094891912,abs=1e-10)


def test_natural_gradient_tolerance_exact_equality_stops_without_step():
    assert 1e-8-.000001/100+.000001/100==1e-8
    r=optimize([1],[1e-8],[-100],[100],[0],[.000001],1)
    assert r['steps']==[] and r['point']==[0] and r['objective']==0


def test_synthetic_log_fault_backtracking_failure_exact_attempt_budget(monkeypatch):
    # Synthetic numerical fault proves guard/budget only, not natural reachability.
    import sugarcode.extra_doc.interior_barrier234 as m
    count=[0]
    def faulty_log(v):
        count[0]+=1
        return 0. if count[0]<=2 else -1000000.
    monkeypatch.setattr(m.math,'log',faulty_log)
    with pytest.raises(ValueError,match='^interior Armijo step not found within 40 reductions$'):
        optimize([1],[1],[-1],[1],[0],[1],1)
    assert count[0]==82
