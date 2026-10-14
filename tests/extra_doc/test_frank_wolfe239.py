import copy
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.frank_wolfe239 import optimize


def test_hand_feasible_segment_exact_line_search_and_nomutation():
    a=[[2,4],[0,0],[1,0],1,1e-9];before=copy.deepcopy(a);r=optimize(*a)
    assert r['point_fraction']==['2/3','1/3'] and r['gap_fraction']=='0' and r['converged_gap_tolerance']
    assert r['steps']==[dict(gradient_fraction=['2','0'],vertex_index=1,direction_fraction=['-1','1'],gap_fraction='2',step_fraction='1/3',point_fraction=['2/3','1/3'])]
    assert r['objective_history_fraction']==['1','2/3'] and r['iterations_used']==1 and not r['global_optimum_claimed'] and r['external_effects']==[] and a==before


def test_400_independent_whole_vertex_scores_and_segment_quadratic_oracles():
    from random import Random
    rng=Random(239)
    for _ in range(400):
        n=rng.randrange(1,9);a=[rng.randrange(1,9) for i in range(n)];b=[rng.randrange(-5,6) for i in range(n)];x=[F(0)]*n;x[rng.randrange(n)]=F(1);initial=list(map(int,x));hist=[sum(F(q,2)*z*z+c*z for q,c,z in zip(a,b,x))];expected=[]
        for _ in range(5):
            gradient=[a[i]*x[i]+b[i] for i in range(n)];vertices=[[F(int(i==j)) for i in range(n)] for j in range(n)];j=min(range(n),key=lambda j:(sum(gradient[i]*vertices[j][i] for i in range(n)),j));d=[vertices[j][i]-x[i] for i in range(n)];gap=sum(gradient[i]*(x[i]-vertices[j][i]) for i in range(n))
            if gap<=F(1,10**9):break
            slope=sum(gradient[i]*d[i] for i in range(n));quad=sum(F(a[i],2)*d[i]**2 for i in range(n));alpha=min(F(1),max(F(0),-slope/(2*quad)));x=[x[i]+alpha*d[i] for i in range(n)];expected.append((gradient,j,d,gap,alpha,x[:]));hist.append(sum(F(q,2)*z*z+c*z for q,c,z in zip(a,b,x)))
        r=optimize(a,b,initial,5,1e-9);assert list(map(F,r['point_fraction']))==x and list(map(F,r['objective_history_fraction']))==hist
        assert sum(x)==1 and all(v>=0 for v in x) and all(v<=u for u,v in zip(hist,hist[1:]))
        assert len(r['steps'])==len(expected)
        for s,(g,j,d,gap,alpha,x) in zip(r['steps'],expected):
            assert s['vertex_index']==j and F(s['step_fraction'])==alpha and F(s['gap_fraction'])==gap
            for key,v in [('gradient_fraction',g),('direction_fraction',d),('point_fraction',x)]:assert list(map(F,s[key]))==v


def test_caps_endpoints_ties_stationary_gap_equality_and_full_step():
    for n in (1,7,8):
        for k in (1,29,30):assert optimize([1000]*n,[0]*n,[1]+[0]*(n-1),k,1)['iterations_used']<=k
    for v in (-1000,1000,-1000.,1000.):optimize([1000],[v],[1],1,1)
    optimize([.000001],[0],[1],1,1e-9)
    r=optimize([1,1],[0,0],[1,0],1,1);assert r['steps']==[] and r['gap_fraction']=='1' and r['converged_gap_tolerance']
    r=optimize([1,1],[100,0],[1,0],1,1e-9);assert r['steps'][0]['step_fraction']=='1' and r['point_fraction']==['0','1']
    assert optimize([1,1],[0,0],[.5,.5],1,1e-9)['steps']==[]


def test_strict_shape_bounds_bool_hugeint_and_simplex_refusals():
    for k in (True,None,1.,0,31,10**400):
        with pytest.raises(ValueError,match='^strict Frank-Wolfe iterations 1..30$'):optimize([1],[0],[1],k,1)
    for x in (None,(),[],True,[0]*9):
        with pytest.raises(ValueError,match='^1..8 simplex coordinates before scan$'):optimize([1],[0],x,1,1)
    for row in (None,(),[],True,[0,0]):
        for slot in (0,1):
            a=[[1],[0],[1],1,1];a[slot]=row
            with pytest.raises(ValueError,match='^one simplex value per dimension$'):optimize(*a)
    for bad in (True,None,'1',-1000.01,1000.01,10**400,-10**400,float('nan'),float('inf')):
        for slot in (0,1,2,4):
            a=[[1,1],[0,0],[1,0],1,1]
            if slot==4:a[4]=bad
            else:a[slot][1]=bad
            with pytest.raises(ValueError,match='^strict finite bounded Frank-Wolfe number$'):optimize(*a)
    for slot,values in ((0,[0,.00000099]),(2,[-.01,1.01]),(4,[0,.00000000099,1.01])):
        for v in values:
            a=[[1],[0],[1],1,1]
            if slot==4:a[4]=v
            else:a[slot][0]=v
            with pytest.raises(ValueError,match='^strict finite bounded Frank-Wolfe number$'):optimize(*a)
    for x in ([0],[.5,.4]):
        with pytest.raises(ValueError,match='^exact simplex coordinate sum must equal one$'):optimize([1]*len(x),[0]*len(x),x,1,1)
