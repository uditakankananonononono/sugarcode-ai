import pytest
from sugarcode.extra_doc.data_warehouse_design import star_rollup as solve

def test_star_rollup_oracle():
    assert solve([[5,9],[2,9],[1,3]],[[5,4],[2,-1],[1,8],[5,0]])=={'label_rollups':[[3,1,8],[9,3,3]],'warehouse_created':False}
    assert solve([[0,0]],[])['label_rollups']==[]
    assert solve([[i,i] for i in range(32)],[[31,4294967295]]*64)['label_rollups']==[[31,64,64*4294967295]]

@pytest.mark.parametrize('d,f,error,message',[(None,[],TypeError,'inputs must be lists or tuples'),([[0,0]],None,TypeError,'inputs must be lists or tuples'),([],[],ValueError,'dimension cap is 32 and fact cap is 64'),([None]*33,[],ValueError,'dimension cap is 32 and fact cap is 64'),([[0,0]],[None]*65,ValueError,'dimension cap is 32 and fact cap is 64'),([[0]],[],ValueError,'records must contain exactly two cells'),([[0,0]],[None],ValueError,'records must contain exactly two cells'),([[0,1],[0,2]],[],ValueError,'dimension keys must be unique'),([[0,0]],[[1,0]],ValueError,'fact key must reference dimension')])
def test_errors(d,f,error,message):
    with pytest.raises(error) as exc:solve(d,f)
    assert str(exc.value)==message

@pytest.mark.parametrize('slot',range(4))
@pytest.mark.parametrize('bad',[True,1.0,None,2**32,-(2**32)])
def test_cells(slot,bad):
    d=[[0,1]];f=[[0,2]];[d,f][slot//2][0][slot%2]=bad
    with pytest.raises(ValueError) as exc:solve(d,f)
    assert str(exc.value)=='cells must be nonbool 32-bit magnitude integers'
