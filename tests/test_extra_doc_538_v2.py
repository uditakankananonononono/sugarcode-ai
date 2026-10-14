import copy
import pytest
from sugarcode.extra_doc.data_mesh_design import mesh_contracts
class L(list): pass
class T(tuple): pass
class I(int): pass

@pytest.mark.parametrize('container',[L,T])
def test_container_subclasses(container):
    for owners,deps in [(container([0,1]),[]),([0,1],container([(0,1)]))]:
        with pytest.raises(TypeError,match='^inputs must be lists or tuples$'):mesh_contracts(owners,deps)
    with pytest.raises(ValueError,match='^dependencies must contain consumer and provider$'):
        mesh_contracts([0,1,2],[(0,1),container((1,2))])


def test_owner_subclass():
    with pytest.raises(ValueError,match='^owners must be nonbool domain indices 0 through 15$'):
        mesh_contracts([0,I(1)],[])

@pytest.mark.parametrize('slot',[0,1])
def test_edge_subclass_nonfirst(slot):
    edge=[1,2];edge[slot]=I(edge[slot])
    with pytest.raises(ValueError,match='^products must be nonbool valid indices$'):
        mesh_contracts([0,1,2],[(0,1),tuple(edge)])


def test_nonadjacent_duplicate_and_mixed_self():
    for edges in [[(0,1),(1,2),(0,1)],[(0,1),(1,1)]]:
        with pytest.raises(ValueError,match='^dependencies must be distinct and nonself$'):
            mesh_contracts([0,1,2],edges)

@pytest.mark.parametrize('outer',[list,tuple])
@pytest.mark.parametrize('row',[list,tuple])
def test_full_contract_plain_containers_and_unchanged(outer,row):
    owners=outer([15,0,15]);deps=outer(row(e) for e in [(2,1),(0,2),(1,0),(0,1)])
    before=copy.deepcopy((owners,deps))
    assert mesh_contracts(owners,deps)=={'cross_domain_products':[[0,1],[1,0],[2,1]],
                                       'domain_contract_counts':[[0,15,1],[15,0,2]],'mesh_deployed':False}
    assert (owners,deps)==before
    assert mesh_contracts(outer([0]),outer())=={'cross_domain_products':[],
                                             'domain_contract_counts':[],'mesh_deployed':False}


def test_last_product_index_and_128_cross_domain_edges():
    owners=[i%2 for i in range(32)]
    edges=[(a,b) for a in range(32) for b in range(32) if owners[a]!=owners[b]][:128]
    result=mesh_contracts(owners,edges)
    assert result['cross_domain_products']==[list(e) for e in sorted(edges)]
    assert sum(c for _,_,c in result['domain_contract_counts'])==128
    assert mesh_contracts(owners,[(31,0)])['cross_domain_products']==[[31,0]]
