import pytest
from sugarcode.extra_doc.etl_pipeline_design import etl_table as solve

def test_filter_projection_and_group_sum_oracle():
    assert solve([[2,10,5],[1,20,4],[2,3,7],[1,-2,5]],2,5,[0,1])=={
      'selected_rows':[[2,10,5],[2,3,7],[1,-2,5]],'projected_rows':[[2,10],[2,3],[1,-2]],
      'group_totals':[[1,-2],[2,13]],'external_load_performed':False}
    assert solve([[0]],0,1,[0,0])['group_totals']==[]
    assert solve([[4294967295]*16]*64,15,4294967295,[0,1])['group_totals']==[[4294967295,64*4294967295]]

@pytest.mark.parametrize('args,error,message',[
 ((None,0,0,[]),TypeError,'inputs must be lists or tuples'),
 (([[0]],0,0,None),TypeError,'inputs must be lists or tuples'),
 (([],0,0,[0,0]),ValueError,'row count must be between 1 and 64'),
 (([None]*65,0,0,[0,0]),ValueError,'row count must be between 1 and 64'),
 (([[]],0,0,[0,0]),ValueError,'rows must contain 1 through 16 cells'),
 (([[None]*17],0,0,[0,0]),ValueError,'rows must contain 1 through 16 cells'),
 (([[0],None],0,0,[0,0]),ValueError,'rows must contain 1 through 16 cells'),
 (([[0],[0,0]],0,0,[0,0]),ValueError,'rows must be rectangular'),
 (([[0]],0,0,[0]),ValueError,'projection must contain exactly two indices'),
 (([[0]],0,0,[0,0,0]),ValueError,'projection must contain exactly two indices'),
])
def test_shapes(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('slot',range(3))
@pytest.mark.parametrize('bad',[True,-1,1,None,'0'])
def test_columns(slot,bad):
    columns=[0,0,0];columns[slot]=bad
    with pytest.raises(ValueError) as exc:solve([[0]],columns[0],0,columns[1:])
    assert str(exc.value)=='columns must be nonbool valid indices'

@pytest.mark.parametrize('bad',[True,2**32,-(2**32),None,1.0])
def test_values(bad):
    with pytest.raises(ValueError) as exc:solve([[0,bad]],0,0,[0,0])
    assert str(exc.value)=='cells and threshold must be nonbool 32-bit magnitude integers'
    with pytest.raises(ValueError) as exc:solve([[0]],0,bad,[0,0])
    assert str(exc.value)=='cells and threshold must be nonbool 32-bit magnitude integers'
