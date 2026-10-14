import pytest
from sugarcode.extra_doc.service_design import service_schedule as solve


def test_dependency_resource_wait_handoff_schedule_oracle():
    r=solve([3,2,4,1],[0,0,1,0],[[],[],[0],[1,2]])
    assert r=={'steps':[{'step_index':0,'resource':0,'start':0,'end':3,'resource_wait':0},
                        {'step_index':1,'resource':0,'start':3,'end':5,'resource_wait':3},
                        {'step_index':2,'resource':1,'start':3,'end':7,'resource_wait':0},
                        {'step_index':3,'resource':0,'start':7,'end':8,'resource_wait':0}],
              'makespan':8,'service_execution_performed':False}
    assert solve([1,2],[7,0],[[1],[]])['steps'][1]['start']==2


def test_max_shapes_duration_boundary_and_cycle():
    assert solve([1000000]*32,[0]*32,[[]]*32)['makespan']==32000000
    with pytest.raises(ValueError,match='^prerequisite graph must be acyclic$'):solve([1,1],[0,0],[[1],[0]])

@pytest.mark.parametrize('args,error,message',[
 ((None,[],[]),TypeError,'inputs must be lists or tuples'),
 (([],[],[]),ValueError,'step count must be between 1 and 32'),
 (([None]*33,[],[]),ValueError,'step count must be between 1 and 32'),
 (([1],[],[[]]),ValueError,'step shapes must agree'),
 (([1],[0],[[None]*33]),ValueError,'prerequisites must be lists or tuples of at most 32'),
 (([True],[0],[[]]),ValueError,'durations must be nonbool integers between 1 and 1000000'),
 (([0],[0],[[]]),ValueError,'durations must be nonbool integers between 1 and 1000000'),
 (([1000001],[0],[[]]),ValueError,'durations must be nonbool integers between 1 and 1000000'),
 (([1],[True],[[]]),ValueError,'resources must be nonbool integers zero through seven'),
 (([1],[-1],[[]]),ValueError,'resources must be nonbool integers zero through seven'),
 (([1],[8],[[]]),ValueError,'resources must be nonbool integers zero through seven'),
 (([1],[0],[[0]]),ValueError,'prerequisites must be nonbool valid nonself indices'),
 (([1,1],[0,0],[[],[0,0]]),ValueError,'prerequisites must be unique'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message
