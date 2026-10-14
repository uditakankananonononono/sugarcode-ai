import copy
import itertools
import pytest
from sugarcode.extra_doc.data_governance import access_matrix
class L(list): pass
class T(tuple): pass
class I(int): pass

@pytest.mark.parametrize('container',[L,T])
def test_container_subclasses(container):
    with pytest.raises(TypeError,match='^rules must be a list or tuple$'):
        access_matrix(2,2,container([(0,0,True)]))
    with pytest.raises(ValueError,match='^rules must contain role asset allow triples$'):
        access_matrix(2,2,[(0,0,True),container((1,1,True))])

@pytest.mark.parametrize('slot',[0,1])
def test_count_subclasses(slot):
    args=[1,1,[]];args[slot]=I(1)
    name,limit=('role',16) if slot==0 else ('asset',32)
    with pytest.raises(ValueError,match='^'+name+' count must be nonbool integer between 1 and '+str(limit)+'$'):
        access_matrix(*args)

@pytest.mark.parametrize('slot',[0,1,2])
def test_rule_subclasses_nonfirst(slot):
    row=[1,1,True];row[slot]=I(row[slot])
    error=TypeError if slot==2 else ValueError
    message=['role must be nonbool valid index','asset must be nonbool valid index','allow must be bool'][slot]
    with pytest.raises(error,match='^'+message+'$'):
        access_matrix(2,2,[(0,0,True),tuple(row)])

@pytest.mark.parametrize('outer',[list,tuple])
@pytest.mark.parametrize('row',[list,tuple])
def test_full_result_containers_unchanged(outer,row):
    rules=outer(row(r) for r in [(0,0,True),(1,1,True),(1,1,False)])
    before=copy.deepcopy(rules)
    assert access_matrix(2,2,rules)=={'allowed_assets':[[0],[]],'permissions_changed':False}
    assert rules==before
    assert access_matrix(1,1,outer())=={'allowed_assets':[[]],'permissions_changed':False}


def test_independent_small_truth_tables():
    for states in itertools.product((None,False,True),repeat=4):
        rules=[(r,a,states[r*2+a]) for r in range(2) for a in range(2) if states[r*2+a] is not None]
        expected=[[a for a in range(2) if states[r*2+a] is True] for r in range(2)]
        assert access_matrix(2,2,rules)=={'allowed_assets':expected,'permissions_changed':False}
        for order in itertools.permutations([(0,0,True),(0,0,False),(1,1,True)]):
            assert access_matrix(2,2,list(order))=={'allowed_assets':[[],[1]],'permissions_changed':False}
