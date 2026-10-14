from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.information_architecture import organize_navigation as solve


def test_two_node_cost_and_cycle_oracle():
    # Four parent tuples: root/root cost5; root/0 cost8; 1/root cost7;1/0 cycle.
    r=solve([2,3],[[-1,1],[-1,0]])
    assert r=={'parents':[-1,-1],'depths':[1,1],'weighted_depth':5,
              'candidate_count':4,'feasible_tree_count':3,'discoverability_validated':False}


def test_deep_chain_depths_and_tie_respects_supplied_order():
    r=solve([F(1,2),1,2],[[-1],[0],[1]])
    assert r['depths']==[1,2,3] and r['weighted_depth']==F(17,2)
    r=solve([0,0],[[1,-1],[-1,0]])
    assert r['parents']==[1,-1] and r['depths']==[2,1]
    # Root reachability may pass through later-index nodes.
    assert solve([1,1,1],[[2],[-1],[1]])['depths']==[3,1,2]


def test_max_shape_boundary_values_and_no_tree():
    r=solve([0]*6,[[-1]+[j for j in range(6) if j!=i][:3] for i in range(6)])
    assert r['candidate_count']==4096 and r['weighted_depth']==0
    for value in [2**32-1,F(2**32-1),F(1,2**32-1)]:
        assert solve([value],[[-1]])['weighted_depth']==value
    with pytest.raises(ValueError,match='^no acyclic rooted navigation exists$'):solve([1,1],[[1],[0]])

@pytest.mark.parametrize('args,error,message',[
 ((None,[]),TypeError,'inputs must be lists or tuples'),
 (([],[]),ValueError,'node count must be between 1 and 6'),
 (([None]*7,[None]*7),ValueError,'node count must be between 1 and 6'),
 (([1],[]),ValueError,'parent options must match node count'),
 (([1],[[]]),ValueError,'each node must have between 1 and 4 parent options'),
 (([1],[[None]*5]),ValueError,'each node must have between 1 and 4 parent options'),
 (([1],[['x']]),ValueError,'parents must be nonbool indices or root -1 and not self'),
 (([1],[[True]]),ValueError,'parents must be nonbool indices or root -1 and not self'),
 (([1],[[0]]),ValueError,'parents must be nonbool indices or root -1 and not self'),
 (([1],[[-2]]),ValueError,'parents must be nonbool indices or root -1 and not self'),
 (([1],[[1]]),ValueError,'parents must be nonbool indices or root -1 and not self'),
 (([1],[[-1,-1]]),ValueError,'parent options must be unique'),
 (([True],[[-1]]),TypeError,'weights must be nonbool int or Fraction'),
 (([-1],[[-1]]),ValueError,'weights must be nonnegative'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('v',[2**32,F(2**32),F(1,2**32)])
def test_bit_refusal(v):
    with pytest.raises(ValueError,match='^weights must fit 32 bits$'):solve([v],[[-1]])
