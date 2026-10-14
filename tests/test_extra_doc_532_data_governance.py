import pytest
from sugarcode.extra_doc.data_governance import access_matrix as solve

def test_deny_precedence_absent_deny_oracle():
    assert solve(2,3,[(0,1,False),(0,1,True),(0,2,True),(1,0,True)])=={'allowed_assets':[[2],[0]],'permissions_changed':False}
    assert solve(16,32,[(15,31,True)]*128)['allowed_assets'][15]==[31]
    assert solve(1,1,[])['allowed_assets']==[[]]

@pytest.mark.parametrize('rules,error,message',[(None,TypeError,'rules must be a list or tuple'),([None]*129,ValueError,'at most 128 rules allowed'),([(0,0)],ValueError,'rules must contain role asset allow triples'),([(0,0,True,0)],ValueError,'rules must contain role asset allow triples'),([(0,0,True),None],ValueError,'rules must contain role asset allow triples'),([(0,0,1)],TypeError,'allow must be bool')])
def test_shapes(rules,error,message):
    with pytest.raises(error) as exc:solve(1,1,rules)
    assert str(exc.value)==message

@pytest.mark.parametrize('slot,limit,name',[(0,16,'role'),(1,32,'asset')])
@pytest.mark.parametrize('kind',['bool','zero','above','none','float'])
def test_counts(slot,limit,name,kind):
    args=[1,1,[]];args[slot]={'bool':True,'zero':0,'above':limit+1,'none':None,'float':1.0}[kind]
    with pytest.raises(ValueError) as exc:solve(*args)
    assert str(exc.value)==name+' count must be nonbool integer between 1 and '+str(limit)

@pytest.mark.parametrize('slot,name',[(0,'role'),(1,'asset')])
@pytest.mark.parametrize('bad',[True,-1,1,None,'0'])
def test_indices(slot,name,bad):
    row=[0,0,True];row[slot]=bad
    with pytest.raises(ValueError) as exc:solve(1,1,[row])
    assert str(exc.value)==name+' must be nonbool valid index'
