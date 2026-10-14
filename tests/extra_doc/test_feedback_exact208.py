import copy
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.feedback_exact208 import simulate


def args():return [[4,2],[[0,-.5],[1,0]],[1,-1],.5,2]


def test_hand_synchronous_coupled_stock_rates_and_balancing_loop():
    a=args();before=copy.deepcopy(a);r=simulate(*a)
    assert r['trace']==[dict(step=0,time_fraction='0',stocks_fraction=['4','2'],rates_fraction=[]),dict(step=1,time_fraction='1/2',stocks_fraction=['4','7/2'],rates_fraction=['0','3']),dict(step=2,time_fraction='1',stocks_fraction=['29/8','5'],rates_fraction=['-3/4','3'])]
    assert r['final_stocks_fraction']==['29/8','5'] and r['feedback_loops']==[dict(stocks=[0,1],gain_fraction='-1/2',kind='balancing')]
    assert a==before and not r['stability_verified'] and r['external_effects']==[]


def test_350_independent_matrix_augmented_recurrence_and_loop_products():
    from random import Random
    rng=Random(208)
    for _ in range(350):
        a=[[rng.randrange(-3,4) for j in range(3)] for i in range(3)];x=[F(rng.randrange(-3,4)) for j in range(3)];u=[rng.randrange(-3,4) for j in range(3)];result=simulate(list(map(int,x)),a,u,.5,3)
        transition=[[F(i==j)+F(a[i][j],2) for j in range(3)] for i in range(3)]
        for k in range(1,4):
            x=[sum(transition[i][j]*x[j] for j in range(3))+F(u[i],2) for i in range(3)]
            assert list(map(F,result['trace'][k]['stocks_fraction']))==x
        for loop in result['feedback_loops']:
            path=loop['stocks'];gain=F(1)
            for i in range(len(path)):gain*=a[path[(i+1)%len(path)]][path[i]]
            assert F(loop['gain_fraction'])==gain and loop['kind']==('reinforcing' if gain>0 else 'balancing')


def test_all_loop_menu_self_three_node_both_directions():
    r=simulate([0]*3,[[1,1,1],[1,-1,1],[1,1,0]],[0]*3,1,0)
    assert {tuple(q['stocks']) for q in r['feedback_loops']}=={(0,),(1,),(0,1),(0,2),(1,2),(0,1,2),(0,2,1)}
    for n in (1,7,8):
        r=simulate([0]*n,[[0]*n for j in range(n)],[0]*n,1,30)
        assert len(r['trace'])==31 and r['feedback_loops']==[]
    for v in (-100,100,-100.0,100.0):simulate([v],[[v]],[v],.000001,1)


def test_all_caps_schema_types_and_huge_integer_refusals():
    for step in (True,1.0,-1,31,None):
        a=args();a[4]=step
        with pytest.raises(ValueError,match='^strict feedback steps 0..30$'):simulate(*a)
    for initial in (None,(),[],True,[0]*9):
        a=args();a[0]=initial
        with pytest.raises(ValueError,match='^1..8 stocks before scan$'):simulate(*a)
    for value in (None,(),[],[0],[0]*3):
        a=args();a[2]=value
        with pytest.raises(ValueError,match='^one feedback value per stock$'):simulate(*a)
        a=args();a[1][0]=value
        with pytest.raises(ValueError,match='^one feedback value per stock$'):simulate(*a)
    for value in (None,(),[],[[1]]):
        a=args();a[1]=value
        with pytest.raises(ValueError,match='^square feedback matrix dimension$'):simulate(*a)
    for bad in (True,None,'1',-100.01,100.01,10**400,-10**400,float('nan'),float('inf')):
        for j in (0,1):
            for index in (0,2):
                a=args();a[index][j]=bad
                with pytest.raises(ValueError,match='^strict finite bounded feedback number$'):simulate(*a)
            a=args();a[1][0][j]=bad
            with pytest.raises(ValueError,match='^strict finite bounded feedback number$'):simulate(*a)
        a=args();a[3]=bad
        with pytest.raises(ValueError,match='^strict finite bounded feedback number$'):simulate(*a)
    for dt in (0,.00000099,1.01):
        a=args();a[3]=dt
        with pytest.raises(ValueError,match='^strict finite bounded feedback number$'):simulate(*a)
