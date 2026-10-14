from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.column_generation import generate_columns as solve


def test_two_row_pattern_column_added_by_negative_reduced_cost():
    r=solve([[1,0],[0,1],[1,1]],[3,3,4],[2,2],[0,1])
    assert r['solution']==[0,0,2] and r['objective']==8
    assert r['trace'][0]['minimum_reduced_cost']==-2 and r['trace'][0]['priced_column']==2
    assert all(v>=0 for v in r['reduced_costs'])
    assert sum(a*b for a,b in zip(r['dual'],[2,2]))==r['objective']
    assert not r['general_lp_solver_claimed']


def test_independent_single_constraint_ratio_oracle_many_columns():
    columns=[[i] for i in range(1,65)];costs=[F(i*i,2) for i in range(1,65)]
    r=solve(columns,costs,[7],[63])
    expected=7*min(c[0]/a[0] for c,a in zip([[v] for v in costs],columns))
    assert r['objective']==expected and r['solution'][0]==7
    assert 2<=r['iterations']<=64


def test_degenerate_zero_demand_and_fractional_pattern():
    assert solve([[1],[2]],[3,4],[0],[0])['objective']==0
    r=solve([[1],[F(3,2)]],[2,2],[3],[0])
    assert r['solution']==[0,2] and r['objective']==4


@pytest.mark.parametrize('args,error,message',[
 ((None,[1],[1],[0]),TypeError,'inputs must be lists or tuples'),
 (([[1]],[1],[],[]),ValueError,'row count must be between 1 and 3'),
 (([[None]]*65,[1]*65,[1],[0]),ValueError,'column count must be between row count and 64'),
 (([[1]],[1],[1],[True]),ValueError,'initial basis must contain distinct nonbool column indices'),
 (([[0]],[1],[1],[0]),ValueError,'columns must be nonnegative and nonzero'),
 (([[1]],[1],[-1],[0]),ValueError,'demand must be nonnegative'),
 (([[1,0],[1,0]],[1,1],[1,1],[0,1]),ValueError,'initial basis must be nonsingular and feasible'),
 (([[1],[2]],[3,4],[1],[0],1),ValueError,'column pricing not closed within iteration cap'),
 (([[1]],[True],[1],[0]),TypeError,'values must be nonbool int or Fraction'),
])
def test_exact_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message


def test_singular_active_candidate_skipped_before_duplicate_optimum():
    r=solve([[1,0],[0,1],[1,0]],[3,2,1],[1,1],[0,1])
    assert r['solution']==[0,1,1] and r['objective']==3 and r['iterations']==2
    assert r['trace'][1]['active_columns']==[0,1,2]


def test_iteration_counts_immediate_and_two_row():
    assert solve([[1]],[2],[3],[0],64)['iterations']==1
    assert solve([[1,0],[0,1],[1,1]],[3,3,4],[2,2],[0,1])['iterations']==2
    assert solve([[1,0,0],[0,1,0],[0,0,1]],[1,2,3],[1,1,1],[0,1,2])['objective']==6

@pytest.mark.parametrize('value',[2**32-1,F(2**32-1),F(1,2**32-1)])
def test_scalar_boundary_admitted(value):assert solve([[1]],[value],[1],[0])['objective']==value

@pytest.mark.parametrize('value',[2**32,F(2**32),F(1,2**32)])
def test_scalar_next_bit_refused(value):
    with pytest.raises(ValueError,match='^rational values must fit 32 bits$'):solve([[1]],[value],[1],[0])

@pytest.mark.parametrize('args,message',[
 (([[1,0,0,0]]*4,[1]*4,[1]*4,[0,1,2,3]),'row count must be between 1 and 3'),
 (([[1]],[],[1],[0]),'cost and basis shapes do not match'),
 (([[1]],[1],[1],[]),'cost and basis shapes do not match'),
 (([[1,2]],[1],[1],[0]),'column must match row count'),
 (([[1]],[1],[1],[-1]),'initial basis must contain distinct nonbool column indices'),
 (([[1]],[1],[1],[1]),'initial basis must contain distinct nonbool column indices'),
 (([[1]],[1],[1],[0.0]),'initial basis must contain distinct nonbool column indices'),
 (([[1,0],[0,1]],[1,1],[1,1],[0,0]),'initial basis must contain distinct nonbool column indices'),
 (([[-1]],[1],[1],[0]),'columns must be nonnegative and nonzero'),
 (([[1,0],[1,1]],[1,1],[0,1],[0,1]),'initial basis must be nonsingular and feasible'),
])
def test_separate_shape_basis_and_feasibility_errors(args,message):
    with pytest.raises(ValueError) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('budget',[65,0,True,1.0,F(1),None,'1'])
def test_iteration_parameter_type_and_bounds(budget):
    with pytest.raises(ValueError) as exc:solve([[1]],[1],[1],[0],budget)
    assert str(exc.value)=='max_iterations must be a nonbool integer between 1 and 64'


def test_exact_cap_first_basis_pricing_tie_and_trace_snapshots():
    r=solve([[1,0],[0,1],[1,1],[1,1]],[3,3,4,4],[2,2],[0,1],2)
    assert r['iterations']==2 and r['trace'][0]['priced_column']==2
    assert r['trace'][0]['active_columns']==[0,1]
    assert r['trace'][1]['active_columns']==[0,1,2]
    assert r['general_lp_solver_claimed'] is False
    # All zero costs: multiple optimal bases, retain first supplied basis.
    r=solve([[1,0],[0,1],[1,1]],[0,0,0],[1,1],[0,1])
    assert r['solution']==[1,1,0]

@pytest.mark.parametrize('args,message',[
 (([[1]],[1],None,[0]),'inputs must be lists or tuples'),
 (([[1]],[1],[1],None),'inputs must be lists or tuples'),
 ((['x'],[1],[1],[0]),'column must match row count'),
])
def test_container_validation(args,message):
    with pytest.raises((ValueError,TypeError)) as exc:solve(*args)
    assert str(exc.value)==message


def test_infeasible_nonsingular_active_candidate_skipped():
    r=solve([[1,0],[0,1],[1,1]],[3,3,4],[1,2],[0,1],2)
    # Basis(0,2) solves(-1,2),must skip; basis(1,2) gives(1,1).
    assert r['solution']==[0,1,1] and r['objective']==7
    assert r['dual']==[1,3]


def test_first_optimal_basis_dual_retained_among_degenerate_ties():
    r=solve([[1,0],[0,1],[1,1]],[3,3,4],[2,2],[0,1])
    # Both (0,2) and (1,2) optimal; first has dual(3,1),second(1,3).
    assert r['dual']==[3,1]
