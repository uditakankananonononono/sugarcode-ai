import copy
import pytest
from fractions import Fraction as F
from sugarcode.extra_doc.fictitious_exact259 import learn


def args():return [[[3,0,-1],[1,2,4]],[1,2],[2,1,1],3]


def test_asymmetric_hand_simultaneous_decisions_no_mutation():
    a=args();before=copy.deepcopy(a);r=learn(*a)
    assert r['history'][0]==dict(round=1,row_action=1,column_action=1,row_expected_fraction=['5/4','2'],column_expected_fraction=['5/3','4/3','7/3'])
    assert r['row_counts']==[1,5] and r['column_counts']==[4,2,1]
    assert r['row_policy_fraction']==['1/6','5/6'] and r['column_policy_fraction']==['4/7','2/7','1/7']
    assert r['zero_sum_gap_fraction']=='8/21' and r['value_fraction']=='71/42'
    assert a==before and r['external_effects']==[] and not r['equilibrium_in_supplied_game']


def test_500_independent_probability_payoff_vote_oracles():
    from random import Random
    rng=Random(259)
    for _ in range(500):
        nr=rng.randrange(2,5);nc=rng.randrange(2,5);m=[[rng.randrange(-5,6) for j in range(nc)] for i in range(nr)];rc=[rng.randrange(1,4) for i in range(nr)];cc=[rng.randrange(1,4) for j in range(nc)];r=learn(m,rc,cc,8);rc=rc[:];cc=cc[:]
        for t,step in enumerate(r['history'],1):
            # Compare unnormalized integer payoff vote totals, avoiding probability normalization.
            rows=[sum(m[i][j]*cc[j] for j in range(nc)) for i in range(nr)]
            cols=[sum(m[i][j]*rc[i] for i in range(nr)) for j in range(nc)]
            i=rows.index(max(rows));j=cols.index(min(cols))
            assert step['round']==t and step['row_action']==i and step['column_action']==j
            assert list(map(F,step['row_expected_fraction']))==[F(v,sum(cc)) for v in rows]
            assert list(map(F,step['column_expected_fraction']))==[F(v,sum(rc)) for v in cols]
            rc[i]+=1;cc[j]+=1
        assert r['row_counts']==rc and r['column_counts']==cc
        row=[F(v,sum(rc)) for v in rc];col=[F(v,sum(cc)) for v in cc]
        high=max(sum(m[i][j]*col[j] for j in range(nc)) for i in range(nr));low=min(sum(m[i][j]*row[i] for i in range(nr)) for j in range(nc))
        assert F(r['zero_sum_gap_fraction'])==high-low and F(r['row_best_value_fraction'])==high and F(r['column_best_value_fraction'])==low
        assert F(r['value_fraction'])==sum(row[i]*m[i][j]*col[j] for i in range(nr) for j in range(nc))


def test_all_caps_priors_zero_and_ties_equilibrium():
    for nr in (2,7,8):
        for nc in (2,7,8):
            r=learn([[1000]*nc]*nr,[1000]+[0]*(nr-1),[1000]+[0]*(nc-1),100)
            assert r['row_counts'][0]==1100 and r['column_counts'][0]==1100 and r['equilibrium_in_supplied_game'] and r['zero_sum_gap_fraction']=='0'
    for v in (-1000,1000,-1000.0,1000.0):learn([[v,v],[v,v]],[1,1],[1,1],1)
    assert learn([[0,0],[0,0]],[1,1],[1,1],99)['history'][-1]['round']==99


def test_strict_menu_shapes_caps_and_huge_values_refused():
    for n in (True,1.0,0,101,None):
        a=args();a[3]=n
        with pytest.raises(ValueError,match='^strict game rounds 1..100$'):learn(*a)
    for m in (None,(),True,[],[[0,0]],[[0,0]]*9):
        a=args();a[0]=m
        with pytest.raises(ValueError,match='^2..8 row actions before scan$'):learn(*a)
    for row in (None,(),True,[],[0],[0]*9):
        a=args();a[0][0]=row
        with pytest.raises(ValueError,match='^2..8 column actions before scan$'):learn(*a)
    for row in (None,(),[],[0],[0]*4):
        a=args();a[0][1]=row
        with pytest.raises(ValueError,match='^rectangular payoff matrix$'):learn(*a)
    for i in (0,1):
        for j in (0,1,2):
            for v in (True,None,'1',-1000.01,1000.01,10**400,-10**400,float('nan'),float('inf')):
                a=args();a[0][i][j]=v
                with pytest.raises(ValueError,match='^strict finite game payoff within -1000..1000$'):learn(*a)
    for index in (1,2):
        for raw in (None,(),[],[1],[1]*4):
            a=args();a[index]=raw
            with pytest.raises(ValueError,match='^one prior count per action$'):learn(*a)
        for j in range(len(args()[index])):
            for v in (True,1.0,'1',None,-1,1001,10**400):
                a=args();a[index][j]=v
                with pytest.raises(ValueError,match='^strict integer prior counts 0..1000$'):learn(*a)
        a=args();a[index]=[0]*len(a[index])
        with pytest.raises(ValueError,match='^positive prior total for each player$'):learn(*a)
