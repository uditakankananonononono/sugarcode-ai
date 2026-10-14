import pytest
from sugarcode.extra_doc.player_experience_design import plan_session as solve


def test_eight_subset_preference_effort_variety_oracle():
    #activity0/1samecategorycannotadjacent;0+2effort3score7;1+2effort4score9overbudget.
    r=solve([(0,1,2),(0,2,4),(1,2,5)],3)
    assert r=={'activity_indices':[0,2],'preference_score':7,'effort':3,
              'feasible_count':5,'engagement_validated':False}


def test_empty_budget_lower_effort_then_lex_ties_and_caps():
    assert solve([(0,1,5)],0)['activity_indices']==[]
    assert solve([(0,2,5),(0,1,5)],2)['activity_indices']==[1]
    assert solve([(0,1,5),(0,1,5)],1)['activity_indices']==[0]
    r=solve([(i%2,1,1000000) for i in range(12)],1000000)
    assert r['activity_indices']==list(range(12)) and r['preference_score']==12000000

@pytest.mark.parametrize('args,error,message',[
 ((None,0),TypeError,'activities must be a list or tuple'),
 (([],0),ValueError,'activity count must be between 1 and 12'),
 (([None]*13,0),ValueError,'activity count must be between 1 and 12'),
 (([None],0),ValueError,'activities must contain category effort and preference'),
 (([(0,1,0)],True),ValueError,'effort_budget must be a nonbool integer zero through 1000000'),
 (([(0,1,0)],-1),ValueError,'effort_budget must be a nonbool integer zero through 1000000'),
 (([(0,1,0)],1000001),ValueError,'effort_budget must be a nonbool integer zero through 1000000'),
 (([(True,1,0)],0),ValueError,'categories must be nonbool integers zero through seven'),
 (([(-1,1,0)],0),ValueError,'categories must be nonbool integers zero through seven'),
 (([(8,1,0)],0),ValueError,'categories must be nonbool integers zero through seven'),
 (([(0,True,0)],0),ValueError,'efforts must be nonbool integers between 1 and 1000000'),
 (([(0,0,0)],0),ValueError,'efforts must be nonbool integers between 1 and 1000000'),
 (([(0,1000001,0)],0),ValueError,'efforts must be nonbool integers between 1 and 1000000'),
 (([(0,1,True)],0),ValueError,'preferences must be nonbool integers zero through 1000000'),
 (([(0,1,-1)],0),ValueError,'preferences must be nonbool integers zero through 1000000'),
 (([(0,1,1000001)],0),ValueError,'preferences must be nonbool integers zero through 1000000'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message
