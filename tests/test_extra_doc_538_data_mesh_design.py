import pytest
from sugarcode.extra_doc.data_mesh_design import mesh_contracts as solve

def test_domain_boundary_oracle():
    assert solve([2,2,1,1],[[3,0],[0,2],[0,1],[1,2],[2,3]])=={
      'cross_domain_products':[[0,2],[1,2],[3,0]],'domain_contract_counts':[[1,2,1],[2,1,2]],'mesh_deployed':False}
    assert solve([0],[])['cross_domain_products']==[]
    edges=[[a,b] for a in range(32) for b in range(32) if a!=b][:128]
    assert solve([15]*32,edges)['domain_contract_counts']==[]

@pytest.mark.parametrize('o,d,error,message',[(None,[],TypeError,'inputs must be lists or tuples'),([0],None,TypeError,'inputs must be lists or tuples'),([],[],ValueError,'product cap is 32 and dependency cap is 128'),([None]*33,[],ValueError,'product cap is 32 and dependency cap is 128'),([0],[None]*129,ValueError,'product cap is 32 and dependency cap is 128'),([0],[None],ValueError,'dependencies must contain consumer and provider'),([0],[[0,0,0]],ValueError,'dependencies must contain consumer and provider'),([0],[[0,0]],ValueError,'dependencies must be distinct and nonself'),([0,1],[[0,1],[0,1]],ValueError,'dependencies must be distinct and nonself')])
def test_errors(o,d,error,message):
    with pytest.raises(error) as exc:solve(o,d)
    assert str(exc.value)==message

@pytest.mark.parametrize('bad',[True,-1,16,1.0,None])
def test_owner(bad):
    with pytest.raises(ValueError) as exc:solve([0,bad],[])
    assert str(exc.value)=='owners must be nonbool domain indices 0 through 15'

@pytest.mark.parametrize('slot',[0,1])
@pytest.mark.parametrize('bad',[True,-1,2,1.0,None])
def test_edge(bad,slot):
    e=[0,1];e[slot]=bad
    with pytest.raises(ValueError) as exc:solve([0,1],[e])
    assert str(exc.value)=='products must be nonbool valid indices'
