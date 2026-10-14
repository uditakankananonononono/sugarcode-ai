import copy
import pytest
from sugarcode.extra_doc.etl_pipeline_design import etl_table
class L(list): pass
class T(tuple): pass
class I(int): pass

@pytest.mark.parametrize('container',[L,T])
def test_all_container_subclasses(container):
    for rows,projection in [(container([[0]]),[0,0]),([[0]],container([0,0]))]:
        with pytest.raises(TypeError,match='^inputs must be lists or tuples$'):
            etl_table(rows,0,0,projection)
    with pytest.raises(ValueError,match='^rows must contain 1 through 16 cells$'):
        etl_table([[0],container([1])],0,0,[0,0])

@pytest.mark.parametrize('slot',range(3))
def test_column_subclasses(slot):
    cols=[0,0,0];cols[slot]=I(0)
    with pytest.raises(ValueError,match='^columns must be nonbool valid indices$'):
        etl_table([[0]],cols[0],0,cols[1:])

@pytest.mark.parametrize('bad',[I(1),True,None,2**32,-2**32,1.0])
def test_mixed_cell_and_threshold_nonfirst(bad):
    with pytest.raises(ValueError,match='^cells and threshold must be nonbool 32-bit magnitude integers$'):
        etl_table([[0,1],[1,bad]],0,0,[0,1])
    with pytest.raises(ValueError,match='^cells and threshold must be nonbool 32-bit magnitude integers$'):
        etl_table([[0,1],[1,2]],0,bad,[0,1])


def test_nonadjacent_rectangular():
    with pytest.raises(ValueError,match='^rows must be rectangular$'):
        etl_table([[0,1],[1,2],[3]],0,0,[0,1])

@pytest.mark.parametrize('outer',[list,tuple])
@pytest.mark.parametrize('row',[list,tuple])
@pytest.mark.parametrize('projection',[list,tuple])
def test_plain_containers_full_contract_and_unchanged(outer,row,projection):
    rows=outer(row(r) for r in [[2,5],[1,4],[2,-5],[0,5]]);proj=projection([0,1])
    before=copy.deepcopy((rows,proj))
    assert etl_table(rows,0,1,proj)=={'selected_rows':[[2,5],[1,4],[2,-5]],
                                   'projected_rows':[[2,5],[1,4],[2,-5]],
                                   'group_totals':[[1,4],[2,0]],'external_load_performed':False}
    assert (rows,proj)==before
    assert etl_table(rows,1,6,proj)=={'selected_rows':[],'projected_rows':[],
                                   'group_totals':[],'external_load_performed':False}

@pytest.mark.parametrize('endpoint',[-(2**32-1),0,2**32-1])
def test_threshold_signed_endpoints_and_repeated_projection(endpoint):
    assert etl_table([[endpoint]],0,endpoint,[0,0])=={
        'selected_rows':[[endpoint]],'projected_rows':[[endpoint,endpoint]],
        'group_totals':[[endpoint,endpoint]],'external_load_performed':False}
