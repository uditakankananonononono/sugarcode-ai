from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.ui_ux_design import optimize_ui_slots as solve


def test_two_action_analytical_swap_oracle():
    r=solve([3,1],[[4,1],[1,2]])
    # identity costs14;swap costs4.
    assert r=={'slots_by_action':[1,0],'weighted_cost':4,'action_costs':[3,1],
              'feasible_assignment_count':2,'global_finite_optimum':True,'usability_validated':False}
    assert solve([3,1],[[4,1],[1,2]],[(0,1)])['weighted_cost']==14


def test_three_action_subset_dynamic_program_oracle():
    w=[F(1,2),3,2];c=[[3,1,5],[2,4,1],[1,3,2]]
    # Independent subset DP: row determined by popcount of already filled slots.
    dp={0:F(0)}
    for mask in range(8):
        if mask not in dp:continue
        i=mask.bit_count()
        if i==3:continue
        for j in range(3):
            if not mask&(1<<j):
                nxt=mask|(1<<j);value=dp[mask]+w[i]*c[i][j]
                dp[nxt]=min(dp.get(nxt,value),value)
    r=solve(w,c)
    assert r['weighted_cost']==dp[7]==F(11,2)
    assert r['slots_by_action']==[1,2,0] and r['feasible_assignment_count']==6


def test_zero_tie_first_lex_assignment_maximum_shape_and_scalar_boundaries():
    r=solve([0]*8,[[0]*8]*8)
    assert r['slots_by_action']==list(range(8)) and r['feasible_assignment_count']==40320
    for v in [2**32-1,F(2**32-1),F(1,2**32-1)]:
        assert solve([v],[[1]],[(0,0)]*0)['weighted_cost']==v
    assert solve([1],[[0]],[(0,0)]*0)['weighted_cost']==0

@pytest.mark.parametrize('args,error,message',[
 ((None,[]),TypeError,'inputs must be lists or tuples'),
 (([],[]),ValueError,'action count must be between 1 and 8'),
 (([None]*9,[None]*9),ValueError,'action count must be between 1 and 8'),
 (([1],[]),ValueError,'cost matrix must be square and match actions'),
 (([1],['0']),ValueError,'cost matrix must be square and match actions'),
 (([1],[[0]],[None]*65),ValueError,'forbidden pair count must not exceed 64'),
 (([1],[[0]],[None]),ValueError,'forbidden pairs must contain action and slot indices'),
 (([1],[[0]],[(True,0)]),ValueError,'forbidden indices must be nonbool integers inside action range'),
 (([1],[[0]],[(0,1)]),ValueError,'forbidden indices must be nonbool integers inside action range'),
 (([True],[[0]]),TypeError,'numbers must be nonbool int or Fraction'),
 (([1],[[1.0]]),TypeError,'numbers must be nonbool int or Fraction'),
 (([-1],[[0]]),ValueError,'weights and costs must be nonnegative'),
 (([1],[[-1]]),ValueError,'weights and costs must be nonnegative'),
 (([1],[[0]],[(0,0)]*64),ValueError,'no feasible UI assignment exists'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('v',[2**32,F(2**32),F(1,2**32)])
def test_next_bit_refusal(v):
    with pytest.raises(ValueError,match='^numbers must fit 32 bits$'):solve([v],[[0]])


def test_negative_forbidden_index_refused_not_silently_ignored():
    with pytest.raises(ValueError) as exc:solve([1],[[0]],[(-1,0)])
    assert str(exc.value)=='forbidden indices must be nonbool integers inside action range'

@pytest.mark.parametrize('field',range(3))
@pytest.mark.parametrize('bad',['x',{},None])
def test_each_container_independently_refused(field,bad):
    args=[[1],[[0]],[]];args[field]=bad
    with pytest.raises(TypeError) as exc:solve(*args)
    assert str(exc.value)=='inputs must be lists or tuples'


def test_long_matrix_row_and_long_forbidden_tuple_errors():
    with pytest.raises(ValueError) as exc:solve([1],[[0,9]])
    assert str(exc.value)=='cost matrix must be square and match actions'
    with pytest.raises(ValueError) as exc:solve([1],[[0]],[(0,0,0)])
    assert str(exc.value)=='forbidden pairs must contain action and slot indices'
