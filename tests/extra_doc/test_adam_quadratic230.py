import copy
import pytest
from sugarcode.extra_doc.adam_quadratic230 import optimize


def args():return [[2,4],[-1,2],[1,-1],.1,.9,.99,.01,4]


def test_350_independent_decimal_adam_full_trace():
    from decimal import Decimal as D,localcontext
    from random import Random
    rng=Random(230)
    with localcontext() as context:
        context.prec=60
        for _ in range(350):
            a=[rng.randint(1,8) for j in range(2)];b=[rng.randint(-3,3) for j in range(2)];x=[D(rng.randint(-3,3)) for j in range(2)];start=list(map(float,x));m=[D(0)]*2;v=[D(0)]*2;lr=D('.1');b1=D('.9');b2=D('.99');eps=D('.01')
            result=optimize(a,b,start,.1,.9,.99,.01,5)
            for t,step in enumerate(result['steps'],1):
                g=[D(q)*z+D(c) for q,z,c in zip(a,x,b)];m=[b1*z+(1-b1)*q for z,q in zip(m,g)];v=[b2*z+(1-b2)*q*q for z,q in zip(v,g)]
                mh=[z/(1-b1**t) for z in m];vh=[z/(1-b2**t) for z in v];scales=[lr/(z.sqrt()+eps) for z in vh];x=[z-scale*q for z,scale,q in zip(x,scales,mh)]
                for key,expected in [('gradient',g),('first_moment',m),('second_moment',v),('corrected_first_moment',mh),('corrected_second_moment',vh),('coordinate_learning_rates',scales),('point',x)]:assert step[key]==pytest.approx(list(map(float,expected)),abs=1e-10)
                assert result['objective_history'][t]==pytest.approx(float(sum(D('.5')*D(q)*z*z+D(c)*z for q,c,z in zip(a,b,x))),abs=1e-10)
            assert result['point']==pytest.approx(list(map(float,x)),abs=1e-10)


def test_nonuniform_adaptation_stationary_axis_t0_bias_and_no_mutation():
    a=args();before=copy.deepcopy(a);r=optimize(*a)
    assert a==before and r['iterations_used']==4 and not r['global_convergence_claimed'] and r['external_effects']==[]
    first=r['steps'][0]
    assert first['gradient']==[1,-2] and first['corrected_first_moment']==pytest.approx([1,-2]) and first['corrected_second_moment']==pytest.approx([1,4])
    assert first['coordinate_learning_rates']==pytest.approx([.1/1.01,.1/2.01])
    assert first['point']==pytest.approx([1-.1/1.01,-1+.2/2.01])
    r=optimize([1,2],[0,0],[0,0],1,0,0,1e-10,1)
    assert r['point']==[0,0] and r['final_gradient']==[0,0] and r['objective_history']==[0,0]
    assert r['method']=='Adam_diagonal_quadratic_FLOAT' and r['objective_definition']=='sum(0.5*a_i*x_i^2 + b_i*x_i)'


def test_full_caps_and_boundary_parameters_nonbool():
    for d in (1,7,8):
        for n in (1,99,100):assert optimize([1]*d,[0]*d,[0]*d,1,.99,.999,1,n)['iterations_used']==n
    for rate in (1e-10,1):
        for eps in (1e-10,1):optimize([.000001],[1000],[-1000],rate,0,0,eps,1)
    optimize([1000],[-1000],[1000],1,.99,.999,1,1)


def test_exact_staged_refusals_at_all_coordinates_and_numeric_inputs():
    for n in (True,1.0,0,101,None):
        a=args();a[7]=n
        with pytest.raises(ValueError,match='^strict Adam iterations 1..100$'):optimize(*a)
    for index,badvalues in ((3,[0,1e-11,1.01]),(4,[-.01,1,.9901]),(5,[-.01,1,.9991]),(6,[0,1e-11,1.01])):
        for bad in badvalues+[True,None,'1',10**400,-10**400,float('nan'),float('inf')]:
            a=args();a[index]=bad
            with pytest.raises(ValueError,match='^strict finite bounded Adam number$'):optimize(*a)
    for init in (None,(),[],[0]*9,True):
        a=args();a[2]=init
        with pytest.raises(ValueError,match='^1..8 Adam coordinates before scan$'):optimize(*a)
    for index in (0,1):
        for bad in (None,(),[],[0],[0]*3):
            a=args();a[index]=bad
            with pytest.raises(ValueError,match='^one Adam value per coordinate$'):optimize(*a)
    for index in (0,1,2):
        for j in (0,1):
            for bad in (True,None,'1',1000.01,-1000.01,10**400,-10**400,float('nan'),float('inf')):
                a=args();a[index][j]=bad
                with pytest.raises(ValueError,match='^strict finite bounded Adam number$'):optimize(*a)
    for value in (0,.00000099,-1):
        a=args();a[0][0]=value
        with pytest.raises(ValueError,match='^strict finite bounded Adam number$'):optimize(*a)


def test_final_gradient_independent_nonzero_linear_terms_and_initial_objective():
    r=optimize(*args())
    assert r['final_gradient']==pytest.approx([2*r['point'][0]-1,4*r['point'][1]+2])
    assert r['objective_history'][0]==0 and [s['step'] for s in r['steps']]==[1,2,3,4]
