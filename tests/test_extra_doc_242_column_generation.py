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
