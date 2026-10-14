import copy
import pytest
from sugarcode.extra_doc.fraud_detection import screen, STATUS_NOTE
class L(list): pass
class T(tuple): pass
class I(int): pass

@pytest.mark.parametrize('container',[L,T])
def test_container_subclasses(container):
    with pytest.raises(ValueError,match='^transactions: list required$'):
        screen(container([(0,1)]),1,1,1)
    with pytest.raises(ValueError,match=r'^transactions\[1\]: \(ts, amount\) required$'):
        screen([(0,1),container((1,2))],1,1,1)

@pytest.mark.parametrize('slot',[0,1])
def test_cell_subclasses_nonfirst(slot):
    row=[1,2];row[slot]=I(row[slot]);name='ts' if slot==0 else 'amount'
    with pytest.raises(ValueError,match=r'^transactions\[1\] '+name+': integer required$'):
        screen([(0,1),tuple(row)],1,1,1)

@pytest.mark.parametrize('slot,name',[(0,'amount_limit'),(1,'max_count'),(2,'window')])
def test_parameter_subclasses(slot,name):
    args=[1,1,1];args[slot]=I(1)
    with pytest.raises(ValueError,match='^'+name+': integer required$'):screen([(0,1)],*args)

@pytest.mark.parametrize('outer',[list,tuple])
@pytest.mark.parametrize('row',[list,tuple])
def test_full_result_simultaneous_rows_and_unchanged(outer,row):
    tx=outer(row(r) for r in [(0,1),(1,1),(1,2),(2,1)]);before=copy.deepcopy(tx)
    result=screen(tx,1,1,1)
    assert result=={'flagged':[{'index':1,'ts':1,'amount':1,'rules':['burst']},
                              {'index':2,'ts':1,'amount':2,'rules':['large','burst']}],
                   'checked':4,'status_note':'PARTIAL: two fixed rules over supplied transactions; a flag is a prompt to review, not a finding of fraud, and unflagged is not cleared'}
    assert result['status_note']==STATUS_NOTE and tx==before
