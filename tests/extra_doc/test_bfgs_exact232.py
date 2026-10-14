import copy
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.bfgs_exact232 import optimize


def test_hand_gradient_hessian_approximation_secant_and_no_mutation():
    a=[[2,4],[-1,2],[1,-1],1];before=copy.deepcopy(a);r=optimize(*a);s=r['steps'][0]
    assert s['gradient_fraction']==['1','-2'] and s['direction_fraction']==['-1','2'] and s['step_size_fraction']=='5/18'
    assert s['displacement_fraction']==['-5/18','5/9'] and s['gradient_change_fraction']==['-5/9','20/9']
    assert s['hessian_before_fraction']==[['1','0'],['0','1']] and s['hessian_after_fraction']==[['46/45','-22/45'],['-22/45','169/45']]
    assert s['secant_verified'] and r['point_fraction']==['13/18','-4/9'] and not r['stationary'] and r['iterations_used']==1 and not r['true_hessian_claimed'] and r['external_effects']==[] and a==before


def test_250_independent_inverse_bfgs_trace_references():
    from random import Random
    rng=Random(232)
    for _ in range(250):
        n=rng.randrange(1,5);a=[rng.randrange(1,8) for i in range(n)];b=[rng.randrange(-3,4) for i in range(n)];x=list(map(F,[rng.randrange(-3,4) for i in range(n)]));initial=x[:];inv=[[F(int(i==j)) for j in range(n)] for i in range(n)];expected=[]
        for k in range(n):
            g=[a[i]*x[i]+b[i] for i in range(n)]
            if not any(g):break
            p=[-sum(inv[i][j]*g[j] for j in range(n)) for i in range(n)];alpha=-sum(g[i]*p[i] for i in range(n))/sum(a[i]*p[i]**2 for i in range(n));s=[alpha*v for v in p];y=[a[i]*s[i] for i in range(n)];rho=1/sum(s[i]*y[i] for i in range(n));left=[[F(int(i==j))-rho*s[i]*y[j] for j in range(n)] for i in range(n)];right=[[F(int(i==j))-rho*y[i]*s[j] for j in range(n)] for i in range(n)]
            inv=[[sum(left[i][k]*inv[k][l]*right[l][j] for k in range(n) for l in range(n))+rho*s[i]*s[j] for j in range(n)] for i in range(n)];x=[u+v for u,v in zip(x,s)];expected.append((g,p,alpha,s,y))
        r=optimize(a,b,list(map(int,initial)),n)
        assert list(map(F,r['point_fraction']))==x and r['stationary'] and x==[F(-b[i],a[i]) for i in range(n)]
        for step,(g,p,alpha,s,y) in zip(r['steps'],expected):
            for key,v in [('gradient_fraction',g),('direction_fraction',p),('displacement_fraction',s),('gradient_change_fraction',y)]:assert list(map(F,step[key]))==v
            assert F(step['step_size_fraction'])==alpha and step['secant_verified']
            h=[list(map(F,row)) for row in step['hessian_after_fraction']]
            assert all(sum(h[i][j]*s[j] for j in range(n))==y[i] for i in range(n))
        assert list(map(F,r['objective_history_fraction']))[-1]==sum(F(a[i],2)*x[i]**2+b[i]*x[i] for i in range(n))


def test_boundaries_stationary_and_caps():
    for n in (1,3,4):
        r=optimize([100]*n,[0]*n,[0]*n,10);assert r['iterations_used']==0 and r['hessian_fraction']==[['1' if i==j else '0' for j in range(n)] for i in range(n)] and r['objective_history_fraction']==['0']
    for v in (-100,100,-100.,100.):optimize([100],[v],[v],1)
    optimize([.001],[0],[1],1)
    for n in (1,9,10):optimize([1],[0],[0],n)


def test_precise_shape_type_hugeint_caps_refusals():
    for k in (True,None,1.,0,11,10**400):
        with pytest.raises(ValueError,match='^strict BFGS iterations 1..10$'):optimize([1],[0],[0],k)
    for x in (None,(),[],True,[0]*5):
        with pytest.raises(ValueError,match='^1..4 BFGS coordinates before scan$'):optimize([1],[0],x,1)
    for row in (None,(),[],True,[0,0]):
        for slot in (0,1):
            a=[[1],[0],[0],1];a[slot]=row
            with pytest.raises(ValueError,match='^one BFGS value per dimension$'):optimize(*a)
    for v in (True,None,'1',-100.01,100.01,10**400,-10**400,float('nan'),float('inf')):
        for slot in (0,1,2):
            a=[[1],[0],[0],1];a[slot][0]=v
            with pytest.raises(ValueError,match='^strict finite bounded BFGS number$'):optimize(*a)
    for v in (0,.00099,-1):
        with pytest.raises(ValueError,match='^strict finite bounded BFGS number$'):optimize([v],[0],[0],1)


def test_one_stationary_axis_and_mixed_invalid_vectors():
    assert not optimize([1,2,4],[0,0,0],[0,1,1],1)['stationary']
    for v in (True,None,'1',100.01,-100.01,10**400):
        for slot in (0,1,2):
            a=[[1,1],[0,0],[0,0],1];a[slot][1]=v
            with pytest.raises(ValueError,match='^strict finite bounded BFGS number$'):optimize(*a)
