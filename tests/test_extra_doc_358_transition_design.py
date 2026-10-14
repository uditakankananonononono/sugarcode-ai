import pytest
from sugarcode.extra_doc.transition_design import transition_portfolio as solve


def test_prerequisite_closed_portfolio_oracle_and_schedule():
    #0cost2benefit1;1cost1benefit9needs0;2cost2benefit5independent,budget3.
    r=solve([2,1,2],[1,9,5],[[],[0],[]],3)
    assert r=={'action_indices':[0,1],'execution_order':[0,1],'cost':3,'benefit':10,
              'feasible_count':4,'systemic_change_validated':False}
    assert solve([1,1],[5,6],[[1],[]],2)['execution_order']==[1,0]


def test_empty_ties_max_shape_and_global_cycles():
    assert solve([1],[1],[[]],0)['action_indices']==[]
    assert solve([2,1],[5,5],[[],[]],2)['action_indices']==[1]
    assert solve([1,1],[5,5],[[],[]],1)['action_indices']==[0]
    assert solve([0]*12,[1000000]*12,[[]]*12,1000000)['feasible_count']==4096
    with pytest.raises(ValueError,match='^prerequisite graph must be acyclic$'):solve([0,0],[0,0],[[1],[0]],0)

@pytest.mark.parametrize('args,error,message',[
 ((None,[],[],0),TypeError,'inputs must be lists or tuples'),
 (([],[],[],0),ValueError,'action count must be between 1 and 12'),
 (([None]*13,[],[],0),ValueError,'action count must be between 1 and 12'),
 (([0],[],[[]],0),ValueError,'action shapes must agree'),
 (([0],[0],[[]],True),ValueError,'budget must be a nonbool integer zero through 1000000'),
 (([0],[0],[[]],-1),ValueError,'budget must be a nonbool integer zero through 1000000'),
 (([0],[0],[[]],1000001),ValueError,'budget must be a nonbool integer zero through 1000000'),
 (([0],[0],[[None]*13],0),ValueError,'prerequisites must be lists or tuples of at most 12'),
 (([True],[0],[[]],0),ValueError,'costs and benefits must be nonbool integers zero through 1000000'),
 (([0],[-1],[[]],0),ValueError,'costs and benefits must be nonbool integers zero through 1000000'),
 (([0],[1000001],[[]],0),ValueError,'costs and benefits must be nonbool integers zero through 1000000'),
 (([0],[0],[[0]],0),ValueError,'prerequisite indices must be nonbool valid nonself indices'),
 (([0,0],[0,0],[[],[0,0]],0),ValueError,'prerequisites must be unique'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message
