from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.bilevel_optimization import solve_bilevel as solve


def test_hierarchy_not_joint_minimum():
    # follower choosesy=2or0;leadercannotsetyindependentlytocostpreferredvalue.
    r=solve([2],[[-4],[0]],[0,1],[[3],[3]],[0],[3])
    assert r['all_follower_responses']==[[2],[0]]
    assert r['all_leader_objectives']==[6,1] and r['leader_index']==1
    assert r['follower_solution']==[0] and r['leader_objective']==1
    assert r['follower_kkt']==[[True],[True]] and not r['general_bilevel_solver_claimed']


def test_independent_follower_grid_reference_and_leader_pick():
    b=[[-8],[-4],[0],[4]];fixed=[0,1,2,3];cost=[[1]]*4
    r=solve([2],b,fixed,cost,[-2],[2])
    responses=[]
    for row in b:responses.append(min((y*y+row[0]*y,y) for y in range(-2,3))[1])
    values=[a+y for a,y in zip(fixed,responses)]
    assert r['all_follower_responses']==[[y] for y in responses]
    assert r['leader_index']==min(range(4),key=values.__getitem__)


def test_fractional_response_box_and_earliest_leader_tie():
    r=solve([3],[[1],[1]],[0,0],[[1],[1]],[-2],[2])
    assert r['follower_solution']==[F(-1,3)] and r['leader_index']==0
    assert solve([1],[[3]],[0],[[1]],[2],[2])['follower_kkt']==[[True]]


@pytest.mark.parametrize('args,error,message',[
 ((None,[[0]],[0],[[0]],[0],[1]),TypeError,'inputs must be lists or tuples'),
 (([],[[]],[0],[[]],[],[]),ValueError,'follower dimension count must be between 1 and 8'),
 (([1],[None]*65,[0]*65,[[0]]*65,[0],[1]),ValueError,'leader option count must be between 1 and 64'),
 (([1],[[0]],[],[[0]],[0],[1]),ValueError,'leader and follower shapes do not match'),
 (([1],[[0,0]],[0],[[0]],[0],[1]),ValueError,'objective row must match follower dimension'),
 (([0],[[0]],[0],[[0]],[0],[1]),ValueError,'follower curvature must be positive'),
 (([1],[[0]],[0],[[0]],[2],[1]),ValueError,'lower bounds must not exceed upper bounds'),
 (([True],[[0]],[0],[[0]],[0],[1]),TypeError,'values must be nonbool int or Fraction'),
])
def test_exact_refusals(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

def test_nonzero_follower_objective_half_factor():
    r=solve([3],[[1]],[0],[[0]],[-2],[2])
    assert r['follower_objective']==F(-1,6)
