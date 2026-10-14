import copy
from fractions import Fraction
import pytest
from sugarcode.extra_doc.data_quality import quality_report
class L(list): pass
class T(tuple): pass
class I(int): pass

@pytest.mark.parametrize('container',[L,T])
def test_container_subclasses(container):
    with pytest.raises(TypeError,match='^rows must be a list or tuple$'):
        quality_report(container([[0]]),0)
    with pytest.raises(ValueError,match='^rows must contain 1 through 16 cells$'):
        quality_report([[0],container([1])],0)


def test_key_column_subclass():
    with pytest.raises(ValueError,match='^key column must be nonbool valid index$'):
        quality_report([[0]],I(0))

@pytest.mark.parametrize('bad',[I(1),True,2**32,-2**32,'0',1.0])
def test_mixed_invalid_cells_nonfirst(bad):
    with pytest.raises(ValueError,match='^cells must be None or nonbool 32-bit magnitude integers$'):
        quality_report([[0,1],[1,bad]],0)


def test_nonadjacent_rectangular_error():
    with pytest.raises(ValueError,match='^rows must be rectangular$'):
        quality_report([[0,1],[1,2],[3]],0)

@pytest.mark.parametrize('outer',[list,tuple])
@pytest.mark.parametrize('row',[list,tuple])
def test_plain_containers_first_duplicate_and_full_contract(outer,row):
    rows=outer(row(r) for r in [[1,None],[2,3],[1,None],[1,None],[None,3]])
    before=copy.deepcopy(rows)
    assert quality_report(rows,0)=={'missing_cells':[[0,1],[2,1],[3,1],[4,0]],
                                   'duplicate_rows':[[0,2],[0,3]],
                                   'duplicate_keys':[[0,2],[0,3]],
                                   'completeness':Fraction(3,5),'accuracy_validated':False}
    assert rows==before

@pytest.mark.parametrize('endpoint',[-(2**32-1),0,2**32-1])
def test_signed_magnitude_endpoints(endpoint):
    assert quality_report([[endpoint]],0)=={'missing_cells':[],'duplicate_rows':[],
                                          'duplicate_keys':[],'completeness':Fraction(1),'accuracy_validated':False}
