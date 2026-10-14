import pytest
from sugarcode.extra_doc.distributed_tracing import analyze_trace as solve

def test_union_child_coverage_oracle():
    assert solve([[-1,0,10],[0,1,6],[0,4,8],[1,2,3]])=={'root':0,'depths':[0,1,1,2],'self_times':[3,4,4,1],'request_observed':False}
    assert solve([[1,4,4],[-1,0,65536]])['self_times']==[0,65536]
    assert solve([[-1,0,0]]+[[0,0,0]]*31)['depths']==[0]+[1]*31

@pytest.mark.parametrize('s,error,message',[(None,TypeError,'spans must be a list or tuple'),([],ValueError,'span count must be between 1 and 32'),([None]*33,ValueError,'span count must be between 1 and 32'),([None],ValueError,'spans must contain parent start end'),([[-1,0]],ValueError,'spans must contain parent start end'),([[-1,0,1],[-1,0,0]],ValueError,'trace must have exactly one root'),([[1,0,0],[0,0,0],[-1,0,0]],ValueError,'span parents must be acyclic'),([[-1,0,5],[0,0,6]],ValueError,'child interval must fit parent'),([[-1,1,5],[0,0,1]],ValueError,'child interval must fit parent')])
def test_errors(s,error,message):
    with pytest.raises(error) as exc:solve(s)
    assert str(exc.value)==message

@pytest.mark.parametrize('slot',range(3))
@pytest.mark.parametrize('bad',[True,None,1.0])
def test_types(slot,bad):
    s=[-1,0,1];s[slot]=bad
    with pytest.raises(ValueError,match='^span values must be nonbool integers$'):solve([s])

@pytest.mark.parametrize('s',[[0,0,1],[1,0,1],[-2,0,1],[-1,-1,1],[-1,2,1],[-1,0,65537]])
def test_bounds(s):
    with pytest.raises(ValueError,match='^span indices and times must be valid$'):solve([s])


def test_nonzero_parent_start_and_zero_child_width():
    assert solve([[-1,5,10],[0,5,7],[0,7,7]])['self_times']==[3,2,0]


def test_contained_sibling_does_not_reduce_union():
    assert solve([[-1,0,10],[0,1,8],[0,2,3]])['self_times']==[3,7,1]
