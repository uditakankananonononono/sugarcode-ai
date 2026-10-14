import copy
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.ant_route214 import generation


def args():return [[[0,2,4],[3,0,1],[2,5,0]],[[1]*3 for _ in range(3)],[0,1],[[0,.5],[.8,0]],.5,6]


def test_hand_directed_routes_costs_synchronous_deposits_no_mutation():
    a=args();before=copy.deepcopy(a);r=generation(*a)
    assert r['tours']==[dict(ant=0,route=[0,1,2,0],cost_fraction='5'),dict(ant=1,route=[1,2,0,1],cost_fraction='5')]
    assert r['pheromone_fraction']==[['1/2','29/10','1/2'],['1/2','1/2','29/10'],['29/10','1/2','1/2']]
    assert r['best_ant']==0 and r['best_route']==[0,1,2,0] and r['best_cost_fraction']=='5' and a==before and not r['global_optimum_claimed'] and r['external_effects']==[]


def test_300_independent_decimal_weighted_route_and_pheromone_oracles():
    from decimal import Decimal as D,localcontext
    from random import Random
    rng=Random(214)
    with localcontext() as context:
        context.prec=60
        for _ in range(300):
            n=rng.randrange(2,6);c=[[0 if i==j else rng.randrange(1,9) for j in range(n)] for i in range(n)];p=[[rng.randrange(1,6) for j in range(n)] for i in range(n)];starts=[rng.randrange(n) for i in range(3)];ds=[[rng.randrange(10)/10 for j in range(n-1)] for i in range(3)];rho=D('.3');q=D(2);increments=[[D(0) for j in range(n)] for i in range(n)];expected=[]
            for ant,(start,draws) in enumerate(zip(starts,ds)):
                route=[start];unseen=list(range(n));unseen.remove(start)
                for draw in draws:
                    weights=[D(p[route[-1]][node])/D(c[route[-1]][node]) for node in unseen];threshold=D(str(draw))*sum(weights);chosen=unseen[-1]
                    for k in range(len(weights)):
                        if sum(weights[:k+1])>threshold:chosen=unseen[k];break
                    route.append(chosen);unseen.remove(chosen)
                route.append(start);cost=sum(c[route[k]][route[k+1]] for k in range(n));expected.append(dict(ant=ant,route=route,cost_fraction=str(cost)))
                for k in range(n):increments[route[k]][route[k+1]]+=q/D(cost)
            r=generation(c,p,starts,ds,float(rho),2);assert r['tours']==expected
            for i in range(n):
                for j in range(n):
                    f=F(r['pheromone_fraction'][i][j]);assert float(f)==pytest.approx(float((1-rho)*p[i][j]+increments[i][j]),abs=1e-12)


def test_boundary_draw_strict_threshold_evaporation_zero_deposit_and_caps():
    a=args();a[1]=[[1]*3 for _ in range(3)];a[0]=[[0,1,1],[1,0,1],[1,1,0]];a[2]=[0];a[3]=[[.5,0]]
    assert generation(*a)['best_route']==[0,2,1,0]
    for n in (2,7,8):
        for ants in (1,19,20):
            r=generation([[0 if i==j else 1000 for j in range(n)] for i in range(n)],[[.000001]*n for i in range(n)],[0]*ants,[[.999999]*(n-1)]*ants,1,0)
            assert r['pheromone_fraction']==[['0']*n]*n and len(r['tours'])==ants
    assert generation([[0,.000001],[1000,0]],[[1000]*2]*2,[1],[[0]],0,1000)['best_route']==[1,0,1]


def test_strict_type_caps_and_staged_numeric_schema_refusals():
    for raw in (None,(),[],True,[[0,1]],[[]]*9):
        a=args();a[0]=raw
        with pytest.raises(ValueError,match='^2..8 routing nodes before scan$'):generation(*a)
    for index in (0,1):
        for raw in (None,(),[],[[]],[[1]*3,[1]*2,[1]*3]):
            a=args();a[index]=raw
            expected='2..8 routing nodes before scan' if index==0 and (type(raw) is not list or len(raw)<2) else 'square ant matrix dimensions'
            with pytest.raises(ValueError,match='^'+expected+'$'):generation(*a)
    for starts in (None,(),[],True,[0]*21):
        a=args();a[2]=starts
        with pytest.raises(ValueError,match='^1..20 ants before scan$'):generation(*a)
    for v in (True,1.0,None,'1',-1,3,10**400):
        a=args();a[2][1]=v
        with pytest.raises(ValueError,match='^strict ant start node indices$'):generation(*a)
    for raw in (None,(),[],[[0,0]]):
        a=args();a[3]=raw
        with pytest.raises(ValueError,match='^one draw row per ant$'):generation(*a)
    for raw in (None,(),[],[0],[0]*3):
        a=args();a[3][1]=raw
        with pytest.raises(ValueError,match='^n-1 draws per ant$'):generation(*a)
    for index in (0,1,3,4,5):
        for bad in (True,None,'1',-.01,1000.01,10**400,-10**400,float('nan'),float('inf')):
            a=args()
            if index in (4,5):a[index]=bad
            else:a[index][0][1]=bad
            with pytest.raises(ValueError,match='^strict finite bounded ant number$'):generation(*a)
    for index,bad in ((1,0),(1,.00000099),(4,1.01)):
        a=args()
        if index==1:a[1][0][0]=bad
        else:a[index]=bad
        with pytest.raises(ValueError,match='^strict finite bounded ant number$'):generation(*a)
    a=args();a[3][0][0]=1
    with pytest.raises(ValueError,match='^ant draw strictly below one$'):generation(*a)
    for i,j in ((0,0),(0,1)):
        a=args();a[0][i][j]=1 if i==j else 0
        with pytest.raises(ValueError,match='^zero diagonal and positive offdiagonal routing costs$'):generation(*a)


def test_draw_decimal_upper_cap_refused_before_strict_one_check():
    a=args();a[3][0][0]=1.01
    with pytest.raises(ValueError,match='^strict finite bounded ant number$'):generation(*a)
