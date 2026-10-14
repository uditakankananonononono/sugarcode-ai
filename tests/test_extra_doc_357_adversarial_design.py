import pytest
from sugarcode.extra_doc.adversarial_design import productive_friction as solve


def test_complete_four_subset_cost_benefit_oracle():
    assert solve([2,3],[3,5],3)=={'feature_indices':[1],'friction':3,'benefit':5,'feasible_count':3,'behavior_change_validated':False}
    assert solve([2,3],[3,5],5)['feature_indices']==[0,1]


def test_ties_zero_and_maximum_caps():
    assert solve([2,1],[5,5],2)['feature_indices']==[1]
    assert solve([1,1],[5,5],1)['feature_indices']==[0]
    assert solve([0],[0],0)['feature_indices']==[]
    assert solve([0],[1],0)['feature_indices']==[0]
    r=solve([0]*12,[1000000]*12,1000000)
    assert r['feasible_count']==4096 and r['benefit']==12000000

@pytest.mark.parametrize('args,error,message',[
 ((None,[],0),TypeError,'friction and benefits must be lists or tuples'),
 (([],[],0),ValueError,'feature count must be between 1 and 12'),
 (([None]*13,[],0),ValueError,'feature count must be between 1 and 12'),
 (([0],[],0),ValueError,'benefit count must match features'),
 (([0],[0],True),ValueError,'budget must be a nonbool integer zero through 1000000'),
 (([0],[0],-1),ValueError,'budget must be a nonbool integer zero through 1000000'),
 (([0],[0],1000001),ValueError,'budget must be a nonbool integer zero through 1000000'),
 (([True],[0],0),ValueError,'friction and benefits must be nonbool integers zero through 1000000'),
 (([0],[-1],0),ValueError,'friction and benefits must be nonbool integers zero through 1000000'),
 (([0],[1000001],0),ValueError,'friction and benefits must be nonbool integers zero through 1000000'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message
