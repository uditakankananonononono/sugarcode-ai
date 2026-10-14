import copy
import pytest
from sugarcode.extra_doc.data_warehouse_design import star_rollup
class L(list): pass
class T(tuple): pass
class I(int): pass

@pytest.mark.parametrize('container',[L,T])
@pytest.mark.parametrize('which',['dimensions','facts'])
def test_container_subclasses(container,which):
    d,f=[(0,1)],[(0,2)]
    with pytest.raises(TypeError,match='^inputs must be lists or tuples$'):
        star_rollup(container(d) if which=='dimensions' else d,
                    container(f) if which=='facts' else f)
    d,f=[(0,1),(1,2)],[(0,2),(1,3)]
    (d if which=='dimensions' else f)[1]=container((1,2))
    with pytest.raises(ValueError,match='^records must contain exactly two cells$'):
        star_rollup(d,f)

@pytest.mark.parametrize('which',['dimensions','facts'])
@pytest.mark.parametrize('slot',[0,1])
@pytest.mark.parametrize('bad',[I(1),True,None,2**32,-2**32,1.0])
def test_scalar_mixed_invalid_nonfirst(which,slot,bad):
    d,f=[(0,1),(1,2)],[(0,2),(1,3)]
    rows=d if which=='dimensions' else f;row=list(rows[1]);row[slot]=bad;rows[1]=tuple(row)
    with pytest.raises(ValueError,match='^cells must be nonbool 32-bit magnitude integers$'):
        star_rollup(d,f)


def test_nonadjacent_duplicate_and_unknown_fact():
    with pytest.raises(ValueError,match='^dimension keys must be unique$'):
        star_rollup([(0,1),(1,2),(0,3)],[])
    with pytest.raises(ValueError,match='^fact key must reference dimension$'):
        star_rollup([(0,1),(1,2)],[(0,1),(1,2),(2,3)])

@pytest.mark.parametrize('outer',[list,tuple])
@pytest.mark.parametrize('row',[list,tuple])
def test_plain_containers_full_contract_unchanged_and_label_merge(outer,row):
    d=outer(row(r) for r in [(0,3),(1,-1),(2,3)])
    f=outer(row(r) for r in [(0,5),(1,1),(2,-5),(0,0)])
    before=copy.deepcopy((d,f))
    assert star_rollup(d,f)=={'label_rollups':[[-1,1,1],[3,3,0]],'warehouse_created':False}
    assert (d,f)==before
    assert star_rollup(d,outer())=={'label_rollups':[],'warehouse_created':False}

@pytest.mark.parametrize('endpoint',[-(2**32-1),0,2**32-1])
def test_signed_magnitude_endpoints(endpoint):
    assert star_rollup([(endpoint,endpoint)],[(endpoint,endpoint)])=={
        'label_rollups':[[endpoint,1,endpoint]],'warehouse_created':False}
