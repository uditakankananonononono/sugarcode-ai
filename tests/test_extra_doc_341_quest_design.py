import pytest
from sugarcode.extra_doc.quest_design import quest_plan as solve


def test_dependency_ancestry_and_schedule_oracle():
    r=solve(['key','door','treasure','unrelated'],[[],[0],[1],[]],[2,3,4,99],2)
    assert r['objective_indices']==[0,1,2] and r['total_effort']==9
    assert r['steps']==[{'objective_index':0,'label':'key','start_effort':0,'end_effort':2},
                        {'objective_index':1,'label':'door','start_effort':2,'end_effort':5},
                        {'objective_index':2,'label':'treasure','start_effort':5,'end_effort':9}]
    assert r['meaning_validated'] is False


def test_ready_tie_later_index_ancestor_max_shape_and_global_cycle():
    assert solve(['a','b','c'],[[2],[],[]],[1]*3,0)['objective_indices']==[2,0]
    assert solve(['a','b','c'],[[],[],[1,0]],[1]*3,2)['objective_indices']==[0,1,2]
    r=solve(['x'*80]*32,[[]]*32,[1000000]*32,31)
    assert r['total_effort']==1000000
    with pytest.raises(ValueError,match='^prerequisite graph must be acyclic$'):
        solve(['a','b','c'],[[],[2],[1]],[1]*3,0)

@pytest.mark.parametrize('args,error,message',[
 ((None,[],[],0),TypeError,'inputs must be lists or tuples'),
 (([],[],[],0),ValueError,'objective count must be between 1 and 32'),
 (([None]*33,[],[],0),ValueError,'objective count must be between 1 and 32'),
 ((['a'],[],[1],0),ValueError,'objective shapes must agree'),
 ((['a'],[[]],[1],True),ValueError,'target must be a nonbool objective index'),
 ((['a'],[[]],[1],1),ValueError,'target must be a nonbool objective index'),
 ((['a'],[[None]*33],[1],0),ValueError,'prerequisite lists must not exceed 32 indices'),
 (([True],[[]],[1],0),TypeError,'labels must be strings'),
 (([''],[[]],[1],0),ValueError,'label length must be between 1 and 80'),
 ((['x'*81],[[]],[1],0),ValueError,'label length must be between 1 and 80'),
 (([' '],[[]],[1],0),ValueError,'labels must not be blank'),
 ((['a'],[[]],[0],0),ValueError,'efforts must be nonbool integers between 1 and 1000000'),
 ((['a'],[[]],[True],0),ValueError,'efforts must be nonbool integers between 1 and 1000000'),
 ((['a'],[[]],[1000001],0),ValueError,'efforts must be nonbool integers between 1 and 1000000'),
 ((['a'],[[0]],[1],0),ValueError,'prerequisites must be nonbool valid nonself indices'),
 ((['a','b'],[[],[0,0]],[1,1],1),ValueError,'prerequisites must be unique'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message
