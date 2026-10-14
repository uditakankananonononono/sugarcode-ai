import copy
import pytest
from sugarcode.extra_doc.ranking_system import rank, STATUS_NOTE
class L(list): pass
class T(tuple): pass
class S(str): pass
class I(int): pass

@pytest.mark.parametrize('container',[L,T])
def test_container_subclasses(container):
    with pytest.raises(ValueError,match='^items: list required$'):rank(container([('a',1)]))
    with pytest.raises(ValueError,match=r'^items\[1\]: \(name, score\) required$'):
        rank([('a',1),container(('b',2))])


def test_scalar_subclasses_nonfirst():
    with pytest.raises(ValueError,match=r'^items\[1\] name: non-empty string up to 40 characters required$'):
        rank([('a',1),(S('b'),2)])
    with pytest.raises(ValueError,match=r'^items\[1\] score: integer required$'):
        rank([('a',1),('b',I(2))])

@pytest.mark.parametrize('outer',[list,tuple])
@pytest.mark.parametrize('row',[list,tuple])
def test_many_ties_full_contract_status_and_unchanged(outer,row):
    items=outer(row(('name_'+str(i).zfill(2),i//6)) for i in reversed(range(24)))
    before=copy.deepcopy(items)
    expected=[]
    for score in reversed(range(4)):
        for i in range(score*6,score*6+6):
            expected.append({'name':'name_'+str(i).zfill(2),'score':score,
                             'rank':(3-score)*6+1,'dense_rank':4-score})
    result=rank(items)
    assert result=={'ranking':expected,'status_note':'PARTIAL: orders supplied scores only; no judgment of whether the scores measure what matters'}
    assert result['status_note']==STATUS_NOTE
    assert items==before
