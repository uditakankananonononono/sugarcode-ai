import copy
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.branch_bound241 import solve


def test_hand_fractional_bound_prunes_and_exact_binary_optimum():
    a=[[2,3,4],[4,5,5],5];before=copy.deepcopy(a);r=solve(*a)
    assert r['selected_bits']==[1,1,0] and r['value_fraction']=='9' and r['weight_fraction']=='5' and r['item_order']==[0,1,2]
    assert r['nodes_pruned_by_bound']>0 and all(F(s['upper_bound_fraction'])<F(s['incumbent_fraction']) for s in r['pruning_trace'])
    assert r['optimal_in_supplied_binary_knapsack'] and r['tie_break']=='lexicographically smallest original-order bit vector' and r['external_effects']==[] and a==before
    assert solve([1,1],[1,1],1)['selected_bits']==[0,1]
    assert solve([1,1],[0,0],2)['selected_bits']==[0,0]


def test_400_independent_exhaustive_binary_subset_references():
    from itertools import product
    from random import Random
    rng=Random(241)
    for _ in range(400):
        n=rng.randrange(1,10);w=[rng.randrange(1,10)/2 for i in range(n)];v=[rng.randrange(0,12)/2 for i in range(n)];cap=rng.randrange(0,20)/2
        feasible=[(sum(F(str(z))*b for z,b in zip(v,bits)),bits) for bits in product((0,1),repeat=n) if sum(F(str(z))*b for z,b in zip(w,bits))<=F(str(cap))]
        best,bits=min(feasible,key=lambda pair:(-pair[0],pair[1]));r=solve(w,v,cap)
        assert r['selected_bits']==list(bits) and F(r['value_fraction'])==best and F(r['weight_fraction'])==sum(F(str(z))*b for z,b in zip(w,bits))
        assert r['item_order']==sorted(range(n),key=lambda i:(-F(str(v[i]))/F(str(w[i])),i)) and r['nodes_visited']>=1
        assert r['nodes_pruned_by_bound']==len(r['pruning_trace']) and all(F(s['upper_bound_fraction'])<F(s['incumbent_fraction']) for s in r['pruning_trace'])


def test_caps_numeric_endpoints_capacity_equal_and_zero():
    for n in (1,15,16):assert solve([1000]*n,[1000]*n,0)['selected_bits']==[0]*n
    for v in (1000,1000.):assert solve([v],[v],v)['selected_bits']==[1]
    assert solve([.000001],[1],.000001)['selected_bits']==[1]
    assert solve([1],[0],1000)['selected_bits']==[0]


def test_strict_shapes_types_bounds_and_hugeints():
    for w in (None,(),[],True,[1]*17):
        with pytest.raises(ValueError,match='^1..16 knapsack items before scan$'):solve(w,[0],1)
    for v in (None,(),[],True,[1,1]):
        with pytest.raises(ValueError,match='^one value per knapsack item$'):solve([1],v,1)
    for bad in (True,None,'1',-.01,1000.01,10**400,-10**400,float('nan'),float('inf')):
        for a in (([bad,1],[1,1],1),([1,1],[1,bad],1),([1,1],[1,1],bad)):
            with pytest.raises(ValueError,match='^strict finite bounded knapsack number$'):solve(*a)
    for v in (0,.00000099):
        with pytest.raises(ValueError,match='^strict finite bounded knapsack number$'):solve([v],[1],1)


def test_exact_pruning_statistics_and_bound_witness_values():
    r=solve([2,3,4],[4,5,5],5)
    assert r['nodes_visited']==6 and r['nodes_pruned_by_bound']==2
    assert r['pruning_trace']==[dict(depth=2,upper_bound_fraction='31/4',incumbent_fraction='9'),dict(depth=1,upper_bound_fraction='15/2',incumbent_fraction='9')]


def test_later_equal_value_larger_bits_cannot_replace_earlier_incumbent():
    # Ratio DFS order [2,1,3,0]: [0,0,1,1] is found before [0,1,0,0].
    r=solve([5,4,2,3],[2,5,3,2],5)
    assert r['item_order']==[2,1,3,0] and r['selected_bits']==[0,0,1,1]
    assert r['value_fraction']=='5' and r['weight_fraction']=='5'


def test_capacity_zero_all_zero_value_optimum_and_exact_counters():
    r=solve([1,2,3],[0,0,0],0)
    assert r['value_fraction']=='0' and r['selected_bits']==[0,0,0] and r['weight_fraction']=='0'
    assert r['nodes_visited']==4 and r['nodes_pruned_by_bound']==0 and r['pruning_trace']==[]


def test_just_below_minimum_weight_exact_refusal():
    with pytest.raises(ValueError,match='^strict finite bounded knapsack number$'):solve([.00000099],[1],1)


def test_narrow_weight_gap_999e_minus9_refused():
    with pytest.raises(ValueError,match='^strict finite bounded knapsack number$'):solve([.000000999],[1],1)
