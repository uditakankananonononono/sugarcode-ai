import pytest
from sugarcode.extra_doc.data_lineage import lineage_sources as solve

def test_join_sources_and_transitive_impact_oracle():
    assert solve([[],[],[0],[1,2],[3]])=={'ultimate_sources':[[0],[1],[0],[0,1],[0,1]],
      'downstream_impact':[[2,3,4],[3,4],[3,4],[4],[]],'lineage_validated':False}
    assert solve([[1],[]])['ultimate_sources']==[[1],[1]]
    assert solve([[]]*32)['ultimate_sources']==[[i] for i in range(32)]

@pytest.mark.parametrize('inputs,error,message',[
 (None,TypeError,'inputs must be a list or tuple'),([],ValueError,'dataset count must be between 1 and 32'),
 ([None]*33,ValueError,'dataset count must be between 1 and 32'),
 ([[],None],ValueError,'datasets must contain at most 32 input indices'),
 ([[None]*33],ValueError,'datasets must contain at most 32 input indices'),
 ([[],[0]*32],ValueError,'input indices must be unique'),([[1],[0]],ValueError,'lineage graph must be acyclic'),
])
def test_shapes(inputs,error,message):
    with pytest.raises(error) as exc:solve(inputs)
    assert str(exc.value)==message

@pytest.mark.parametrize('bad',[True,1.0,-1,2,None,'1'])
def test_nonself_validrange_type(bad):
    with pytest.raises(ValueError) as exc:solve([[bad],[]])
    assert str(exc.value)=='inputs must contain nonbool valid nonself indices'

def test_self():
    with pytest.raises(ValueError,match='^inputs must contain nonbool valid nonself indices$'):solve([[0]])
