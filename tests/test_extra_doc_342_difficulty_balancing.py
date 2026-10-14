import pytest
from sugarcode.extra_doc.difficulty_balancing import balance_difficulty as solve


def test_complete_four_curve_objective_and_transition_oracle():
    #2/3/4error1,2/5/4decreasing,4/3/4decreasing,4/5/4decreasing.
    r=solve([[2,4],[3,5],[4]],[2,4,4],2)
    assert r=={'difficulty_levels':[2,3,4],'squared_error':1,'player_experience_validated':False}
    assert solve([[1,3],[2,4]],[3,4],1)['difficulty_levels']==[3,4]
    assert solve([[3,1]],[2],0)['difficulty_levels']==[1]


def test_equal_levels_max_caps_and_infeasible():
    assert solve([[0],[100]],[0,100],100)['squared_error']==0
    assert solve([list(range(8))]*32,[0]*32,0)['difficulty_levels']==[0]*32
    with pytest.raises(ValueError,match='^no nondecreasing curve satisfies increase cap$'):
        solve([[2],[1]],[2,1],100)
    with pytest.raises(ValueError,match='^no nondecreasing curve satisfies increase cap$'):
        solve([[0],[2]],[0,2],1)

@pytest.mark.parametrize('args,error,message',[
 ((None,[],0),TypeError,'options and targets must be lists or tuples'),
 (([],[],0),ValueError,'stage count must be between 1 and 32'),
 (([None]*33,[],0),ValueError,'stage count must be between 1 and 32'),
 (([[0]],[],0),ValueError,'target count must match stages'),
 (([[]],[0],0),ValueError,'each stage must have between 1 and 8 levels'),
 (([[None]*9],[0],0),ValueError,'each stage must have between 1 and 8 levels'),
 (([[0]],[0],True),ValueError,'max_increase must be a nonbool integer zero through 100'),
 (([[0]],[0],-1),ValueError,'max_increase must be a nonbool integer zero through 100'),
 (([[0]],[0],101),ValueError,'max_increase must be a nonbool integer zero through 100'),
 (([[0]],[True],0),ValueError,'targets must be nonbool integers zero through 100'),
 (([[0]],[-1],0),ValueError,'targets must be nonbool integers zero through 100'),
 (([[0]],[101],0),ValueError,'targets must be nonbool integers zero through 100'),
 (([[True]],[0],0),ValueError,'levels must be nonbool integers zero through 100'),
 (([[-1]],[0],0),ValueError,'levels must be nonbool integers zero through 100'),
 (([[101]],[0],0),ValueError,'levels must be nonbool integers zero through 100'),
 (([[0,0]],[0],0),ValueError,'levels must be unique'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message
