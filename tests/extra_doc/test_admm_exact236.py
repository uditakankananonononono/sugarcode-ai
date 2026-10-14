import copy
import pytest
from fractions import Fraction as F
from sugarcode.extra_doc.admm_exact236 import solve


def args():return [[2,3],[3,-4],1,2,[0,0],30,1e-9]


def test_hand_one_step_split_soft_threshold_and_dual_update():
    a=args();a[5]=1;before=copy.deepcopy(a);r=solve(*a)
    assert r['trace']==[dict(step=1,x_fraction=['3/4','-4/5'],z_fraction=['1/4','-3/10'],scaled_dual_fraction=['1/2','-1/2'],primal_infinity_fraction='1/2',dual_infinity_fraction='3/5')]
    assert r['solution_fraction']==['1/4','-3/10'] and r['objective_fraction']=='-481/400'
    assert r['kkt_infinity_fraction']=='21/10' and not r['converged_residual_tolerance'] and r['iterations_used']==1
    assert r['rho_fraction']=='2' and r['penalty_fraction']=='1' and a==before and not r['global_optimum_claimed'] and r['external_effects']==[]


def test_300_independent_exact_scalar_piecewise_oracle_all_steps():
    from random import Random
    rng=Random(236)
    for _ in range(300):
        a=rng.randrange(1,8);b=rng.randrange(-8,9);pen=rng.randrange(4);rho=rng.randrange(1,6);z=F(rng.randrange(-2,3));u=F(0);tol=F(1,10**9);trace=[]
        result=solve([a],[b],pen,rho,[int(z)],10,float(tol))
        for t in range(1,11):
            # Solve scalar quadratic derivative, then solve three L1 sign regions.
            x=(b+rho*z-rho*u)/F(a+rho);v=x+u;old=z
            if v*rho>pen:z=v-F(pen,rho)
            elif v*rho<-pen:z=v+F(pen,rho)
            else:z=F(0)
            u=u+x-z;primal=abs(x-z);dual=rho*abs(z-old)
            got=result['trace'][t-1]
            assert list(map(F,got['x_fraction']))==[x] and list(map(F,got['z_fraction']))==[z] and list(map(F,got['scaled_dual_fraction']))==[u]
            assert F(got['primal_infinity_fraction'])==primal and F(got['dual_infinity_fraction'])==dual
            if primal<=tol and dual<=tol:break
        assert F(result['objective_fraction'])==F(a,2)*z*z-b*z+pen*abs(z)
        g=a*z-b;expected=abs(g+pen) if z>0 else abs(g-pen) if z<0 else max(abs(g)-pen,0)
        assert F(result['kkt_infinity_fraction'])==expected


def test_zero_equality_threshold_positive_negative_and_convergence():
    for b in (-1,0,1):
        r=solve([1],[b],1,1,[0],1,1)
        assert r['solution_fraction']==['0'] and r['converged_residual_tolerance']
    r=solve(*args());assert list(map(float,map(F,r['solution_fraction'])))==pytest.approx([1,-1],abs=1e-6)
    assert r['method']=='exact rational diagonal quadratic L1 ADMM'
    assert r['stopping_contract']=='absolute infinity primal and dual residuals <= supplied tolerance'


def test_caps_numeric_endpoints_and_no_mutation():
    for d in (1,7,8):
        for n in (1,29,30):
            a=[[1]*d,[0]*d,0,1,[0]*d,n,1e-9];before=copy.deepcopy(a)
            assert solve(*a)['iterations_used']==1 and a==before
    for v in (-1000,1000,-1000.0,1000.0):solve([1000],[v],1000,1000,[v],1,1)
    solve([.000001],[0],0,.000001,[0],1,1e-9)


def test_strict_caps_shapes_and_every_numeric_oversize_refusal_stage():
    for n in (True,1.0,0,31,None):
        a=args();a[5]=n
        with pytest.raises(ValueError,match='^strict ADMM iterations 1..30$'):solve(*a)
    for init in (True,None,(),[],[0]*9):
        a=args();a[4]=init
        with pytest.raises(ValueError,match='^1..8 ADMM coordinates before scan$'):solve(*a)
    for index in (0,1):
        for v in (True,None,(),[],[0],[0]*3):
            a=args();a[index]=v
            with pytest.raises(ValueError,match='^one ADMM value per coordinate$'):solve(*a)
    for index in (0,1,4):
        for j in (0,1):
            for v in (True,None,'1',-1000.01,1000.01,10**400,-10**400,float('nan'),float('inf')):
                a=args();a[index][j]=v
                with pytest.raises(ValueError,match='^strict finite bounded ADMM number$'):solve(*a)
    for index in (2,3,6):
        for v in (True,None,'1',-.01,1000.01,10**400,-10**400,float('nan'),float('inf')):
            a=args();a[index]=v
            with pytest.raises(ValueError,match='^strict finite bounded ADMM number$'):solve(*a)
    for index,bads in ((0,[0,.00000099]),(3,[0,.00000099]),(6,[0,.00000000099,1.01])):
        for v in bads:
            a=args()
            if index==0:a[0][0]=v
            else:a[index]=v
            with pytest.raises(ValueError,match='^strict finite bounded ADMM number$'):solve(*a)


def test_each_residual_equal_tolerance_is_converged():
    for penalty in (0,1):
        r=solve([1],[2],penalty,1,[0],1,1)
        assert r['converged_residual_tolerance'] and r['iterations_used']==1
        assert r['trace'][0]['primal_infinity_fraction']==('0' if penalty==0 else '1')
        assert r['trace'][0]['dual_infinity_fraction']==('1' if penalty==0 else '0')
