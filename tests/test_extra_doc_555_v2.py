import copy
import pytest
from sugarcode.extra_doc.image_components import components, STATUS_NOTE
class L(list): pass
class T(tuple): pass
class I(int): pass
@pytest.mark.parametrize('container',[L,T])
def test_container_subclasses(container):
    with pytest.raises(ValueError,match='^image: list of rows required$'):components(container([[1]]))
    with pytest.raises(ValueError,match=r'^image\[1\]: list required$'):components([[1],container([0])])
def test_cell_and_connectivity_subclasses():
    with pytest.raises(ValueError,match=r'^image\[1\]\[1\]: integer required$'):components([[0,1],[0,I(1)]])
    with pytest.raises(ValueError,match='^connectivity: integer required$'):components([[1]],I(4))
@pytest.mark.parametrize('outer',[list,tuple])
@pytest.mark.parametrize('row',[list,tuple])
def test_full_default_diagonal_contract_status_and_unchanged(outer,row):
    image=outer(row(r) for r in [[1,0,0],[0,1,0],[0,0,1]]);before=copy.deepcopy(image)
    result=components(image)
    assert result=={'count':3,'components':[{'size':1,'bbox':(0,0,0,0)},
                                          {'size':1,'bbox':(1,1,1,1)},
                                          {'size':1,'bbox':(2,2,2,2)}],
                   'rows':3,'cols':3,'status_note':'PARTIAL: connected foreground cells on a supplied binary grid only; no object recognition, grey levels, noise handling or understanding of what the image shows'}
    assert result['status_note']==STATUS_NOTE and result==components(image,4)
    assert components(image,8)['components']==[{'size':3,'bbox':(0,0,2,2)}]
    assert image==before
