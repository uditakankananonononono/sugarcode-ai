from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.data_quality import quality_report as solve

def test_missing_duplicates_key_distinction_oracle():
    assert solve([[1,None],[1,2],[1,2],[None,2]],0)=={'missing_cells':[[0,1],[3,0]],'duplicate_rows':[[1,2]],
      'duplicate_keys':[[0,1],[0,2]],'completeness':F(3,4),'accuracy_validated':False}
    assert solve([[4294967295]*16]*64,15)['completeness']==1
    assert solve([[None]],0)['completeness']==0

@pytest.mark.parametrize('rows,error,message',[(None,TypeError,'rows must be a list or tuple'),([],ValueError,'row count must be between 1 and 64'),([None]*65,ValueError,'row count must be between 1 and 64'),([[]],ValueError,'rows must contain 1 through 16 cells'),([[None]*17],ValueError,'rows must contain 1 through 16 cells'),([[0],None],ValueError,'rows must contain 1 through 16 cells'),([[0],[0,0]],ValueError,'rows must be rectangular')])
def test_shapes(rows,error,message):
    with pytest.raises(error) as exc:solve(rows,0)
    assert str(exc.value)==message

@pytest.mark.parametrize('bad',[True,-1,1,None,'0'])
def test_column(bad):
    with pytest.raises(ValueError) as exc:solve([[0]],bad)
    assert str(exc.value)=='key column must be nonbool valid index'

@pytest.mark.parametrize('bad',[True,2**32,-(2**32),'0',1.0])
def test_values(bad):
    with pytest.raises(ValueError) as exc:solve([[0,bad]],0)
    assert str(exc.value)=='cells must be None or nonbool 32-bit magnitude integers'
