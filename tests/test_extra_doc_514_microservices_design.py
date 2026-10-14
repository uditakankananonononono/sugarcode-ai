import pytest
from sugarcode.extra_doc.microservices_design import service_partition as solve


def test_balanced_partition_directional_coupling_oracle():
    matrix=[[0,9,1,0],[8,0,0,1],[2,0,0,7],[0,3,6,0]]
    assert solve(matrix,2)=={'services':[[0,1],[2,3]],'cross_coupling':7,'decomposition_performed':False}
    assert solve([[0]*4]*4,3)['services']==[[0,2,3],[1]]
    assert solve([[0]*3]*3,1) is None
    assert solve([[1000]*12]*12,6)['cross_coupling']==72000
    assert solve([[0,0],[0,0]],1)['services']==[[0],[1]]

@pytest.mark.parametrize('matrix,error,message',[
 (None,TypeError,'coupling must be a list or tuple'),([[0]],ValueError,'component count must be between 2 and 12'),
 ([None]*13,ValueError,'component count must be between 2 and 12'),
 ([[0],[0]],ValueError,'coupling must be square'),([[0,0,0],[0,0]],ValueError,'coupling must be square'),
 ([[0,0],None],ValueError,'coupling must be square'),
])
def test_shapes(matrix,error,message):
    with pytest.raises(error) as exc:solve(matrix,1)
    assert str(exc.value)==message

@pytest.mark.parametrize('bad',[True,0,13,None,1.0])
def test_size(bad):
    with pytest.raises(ValueError) as exc:solve([[0]*2]*2,bad)
    assert str(exc.value)=='maximum size must be nonbool integer between 1 and 12'

@pytest.mark.parametrize('bad',[True,-1,1001,None,1.0])
def test_values(bad):
    with pytest.raises(ValueError) as exc:solve([[0,bad],[0,0]],1)
    assert str(exc.value)=='coupling must be nonbool integers zero through 1000'
