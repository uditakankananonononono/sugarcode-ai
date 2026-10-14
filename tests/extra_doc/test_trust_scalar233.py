from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.trust_scalar233 import optimize


def test_hand_negative_curvature_boundary_rejection_shrink_accept_expand():
    r=optimize(0,0,2,1);s=r['steps'][0]
    assert s==dict(initial_radius_fraction='2',gradient_fraction='0',hessian_fraction='-4',step_fraction='-2',predicted_reduction_fraction='8',actual_reduction_fraction='-8',ratio_fraction='-1',accepted=False,point_fraction='0',next_radius_fraction='1/2')
    assert r['point_fraction']=='0' and r['objective_history_fraction']==['1','1'] and r['iterations_used']==1 and not r['global_optimum_claimed'] and r['external_effects']==[]
    s=optimize(0,0,.5,1)['steps'][0];assert s['step_fraction']=='-1/2' and s['ratio_fraction']=='7/8' and s['accepted'] and s['next_radius_fraction']=='1'
    assert optimize(1,0,1,30)['steps']==[]


def test_400_independent_derivative_polynomial_model_candidates_references():
    from random import Random
    rng=Random(233)
    for _ in range(400):
        x=F(rng.randrange(-6,7),2);b=F(rng.randrange(-6,7),2);delta=F(rng.randrange(1,9),2);start=x;initial_radius=delta;expected=[];hist=[str(x**4-2*x*x+1+b*x)]
        for i in range(4):
            g=4*x**3-4*x+b;h=12*x*x-4
            def model(p):return g*p+(h/2)*p*p
            points={-delta,delta,F(0)}
            if h>0:
                vertex=-g/h
                if abs(vertex)<=delta:points.add(vertex)
            p=min(points,key=lambda p:(model(p),p));pred=-model(p)
            if pred<=0:break
            actual=-(4*x**3*p+6*x*x*p*p+4*x*p**3+p**4-4*x*p-2*p*p+b*p);ratio=actual/pred;old=delta;accepted=ratio>F(1,10)
            if ratio<F(1,4):delta/=4
            elif ratio>F(3,4) and abs(p)==old:delta=min(delta*2,10)
            if accepted:x+=p
            expected.append((p,pred,actual,ratio,accepted,old,delta,x,g,h));hist.append(str(x**4-2*x*x+1+b*x))
        r=optimize(float(start),float(b),float(initial_radius),4)
        assert r['point_fraction']==str(x) and r['objective_history_fraction']==hist and r['iterations_used']==len(expected)
        for s,row in zip(r['steps'],expected):
            for key,v in zip(('step_fraction','predicted_reduction_fraction','actual_reduction_fraction','ratio_fraction','accepted','initial_radius_fraction','next_radius_fraction','point_fraction','gradient_fraction','hessian_fraction'),row):assert s[key]==(v if type(v) is bool else str(v))


def test_numeric_iteration_endpoints_and_caps():
    for v in (-10,10,-10.,10.):optimize(v,v,10,1)
    optimize(1,0,.001,1)
    for k in (1,29,30):optimize(1,0,1,k)


def test_strict_refusals_nonbool_hugeints():
    for v in (True,None,'1',-10.01,10.01,10**400,-10**400,float('nan'),float('inf')):
        for slot in range(3):
            a=[0,0,1,1];a[slot]=v
            with pytest.raises(ValueError,match='^strict finite bounded trust number$'):optimize(*a)
    for v in (0,.00099,-1):
        with pytest.raises(ValueError,match='^strict finite bounded trust number$'):optimize(0,0,v,1)
    for k in (True,None,1.,0,31,10**400):
        with pytest.raises(ValueError,match='^strict trust iterations 1..30$'):optimize(0,0,1,k)


def test_exact_ratio_thresholds_and_shrink_threshold_gap():
    s=optimize(-1,8.01,.9,1)['steps'][0];assert s['ratio_fraction']=='1/10' and not s['accepted']
    s=optimize(-1,7.296,.8,1)['steps'][0];assert s['ratio_fraction']=='1/4' and s['next_radius_fraction']=='4/5'
    s=optimize(-.6,4.14,1.1,1)['steps'][0];assert s['ratio_fraction']=='23/100' and s['next_radius_fraction']=='11/40'
    s=optimize(-1.2,8.096,.4,1)['steps'][0];assert s['ratio_fraction']=='3/4' and s['next_radius_fraction']=='2/5'
