import copy
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.proximal_exact238 import optimize


def test_hand_forward_softthreshold_nonsmooth_kkt_and_nomutation():
    a=[[2,4],[-3,4],1,[0,0],1,1e-9];before=copy.deepcopy(a);r=optimize(*a)
    assert r['point_fraction']==['1/2','-3/4'] and r['step_size_fraction']=='1/4' and r['kkt_fraction']==['1','0'] and not r['converged_kkt_tolerance']
    assert r['steps']==[dict(gradient_fraction=['-3','4'],forward_point_fraction=['3/4','-1'],point_fraction=['1/2','-3/4'],threshold_fraction='1/4',kkt_before_fraction=['2','3'])]
    assert r['objective_history_fraction']==['0','-15/8'] and r['iterations_used']==1 and not r['global_optimum_claimed'] and r['external_effects']==[] and a==before


def test_400_independent_piecewise_proximal_scalar_minima_traces():
    from random import Random
    rng=Random(238)
    for _ in range(400):
        n=rng.randrange(1,9);a=[rng.randrange(1,9) for i in range(n)];b=[rng.randrange(-6,7) for i in range(n)];pen=rng.randrange(4);x=list(map(F,[rng.randrange(-2,3) for i in range(n)]));initial=x[:];rate=F(1,max(a));hist=[sum(F(q,2)*z*z+c*z+pen*abs(z) for q,c,z in zip(a,b,x))];expected=[]
        def kkt(v):return [abs(q*z+c+pen) if z>0 else abs(q*z+c-pen) if z<0 else max(abs(c)-pen,0) for q,c,z in zip(a,b,v)]
        for _ in range(5):
            if max(kkt(x))<=F(1,10**9):break
            g=[q*z+c for q,c,z in zip(a,b,x)];raw=[z-rate*v for z,v in zip(x,g)];new=[]
            for v in raw:
                # Independent scalar prox solve: minimize piecewise squared distance+L1.
                candidates=[F(0),max(F(0),v-rate*pen),min(F(0),v+rate*pen)]
                new.append(min(candidates,key=lambda z:(z-v)**2/(2*rate)+pen*abs(z)))
            expected.append((g,raw,new,kkt(x)));x=new;hist.append(sum(F(q,2)*z*z+c*z+pen*abs(z) for q,c,z in zip(a,b,x)))
        r=optimize(a,b,pen,list(map(int,initial)),5,1e-9)
        assert list(map(F,r['point_fraction']))==x and list(map(F,r['objective_history_fraction']))==hist and list(map(F,r['kkt_fraction']))==kkt(x)
        assert r['converged_kkt_tolerance']==(max(kkt(x))<=F(1,10**9)) and all(v<=u for u,v in zip(hist,hist[1:]))
        for s,(g,raw,new,kk) in zip(r['steps'],expected):
            for key,v in [('gradient_fraction',g),('forward_point_fraction',raw),('point_fraction',new),('kkt_before_fraction',kk)]:assert list(map(F,s[key]))==v


def test_thresholds_tolerance_equal_zero_penalty_and_caps():
    for b in (-1,0,1):assert optimize([1],[b],1,[0],1,1e-9)['steps']==[]
    for b in (-2,2):assert optimize([1],[b],1,[0],1,1)['steps']==[]
    for n in (1,7,8):
        for k in (1,49,50):assert optimize([1000]*n,[0]*n,0,[0]*n,k,1)['iterations_used']==0
    for v in (-1000,1000,-1000.,1000.):optimize([1000],[v],1000,[v],1,1)
    optimize([.000001],[0],0,[0],1,1e-9)
    assert optimize([1],[0],0,[1],1,1e-9)['point_fraction']==['0']


def test_strict_types_shapes_bounds_hugeints():
    for k in (True,None,1.,0,51,10**400):
        with pytest.raises(ValueError,match='^strict proximal iterations 1..50$'):optimize([1],[0],0,[0],k,1)
    for initial in (None,(),[],True,[0]*9):
        with pytest.raises(ValueError,match='^1..8 proximal coordinates before scan$'):optimize([1],[0],0,initial,1,1)
    for row in (None,(),[],True,[0,0]):
        for slot in (0,1):
            a=[[1],[0],0,[0],1,1];a[slot]=row
            with pytest.raises(ValueError,match='^one proximal value per dimension$'):optimize(*a)
    for bad in (True,None,'1',-1000.01,1000.01,10**400,-10**400,float('nan'),float('inf')):
        for slot in (0,1,2,3,5):
            a=[[1,1],[0,0],0,[0,0],1,1]
            if slot in (0,1,3):a[slot][1]=bad
            else:a[slot]=bad
            with pytest.raises(ValueError,match='^strict finite bounded proximal number$'):optimize(*a)
    for slot,values in ((0,[0,.00000099]),(2,[-.01]),(5,[0,.00000000099,1.01])):
        for v in values:
            a=[[1],[0],0,[0],1,1]
            if slot==0:a[0][0]=v
            else:a[slot]=v
            with pytest.raises(ValueError,match='^strict finite bounded proximal number$'):optimize(*a)


def test_kkt_tolerance_exact_equality_reported_converged():
    r=optimize([1],[2],1,[0],1,1)
    assert r['kkt_fraction']==['1'] and r['converged_kkt_tolerance'] and r['steps']==[]
