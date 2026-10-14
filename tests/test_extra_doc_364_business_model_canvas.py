import pytest
from sugarcode.extra_doc.business_model_canvas import map_canvas as solve


def test_nine_block_membership_cycle_reach_and_isolation_oracle():
    blocks=[[name] for name in ('p','a','r','v','rel','ch','s','c','rev')]
    r=solve(blocks,[(0,1),(1,2),(2,0),(3,4),(4,5)])
    assert [node['block'] for node in r['nodes']]==['partners','activities','resources','value_propositions','relationships','channels','segments','costs','revenues']
    assert [node['entry'] for node in r['nodes']]==['p','a','r','v','rel','ch','s','c','rev']
    assert r['links']==[[0,1],[1,2],[2,0],[3,4],[4,5]]
    assert r['reachable']==[[1,2],[0,2],[0,1],[4,5],[5],[],[],[],[]]
    assert r['isolated']==[6,7,8]
    assert r['business_viability_validated'] is False
    assert solve([[]]*9,[])['nodes']==[]


def test_caps_admitted():
    blocks=[['W'*64]*8]*9
    links=[(i,j) for i in range(72) for j in range(72) if i!=j][:128]
    r=solve(blocks,links)
    assert len(r['nodes'])==72 and len(r['links'])==128
    assert solve([['x'],['y']]+[[]]*7,[(1,0)])['reachable']==[[],[0]]

@pytest.mark.parametrize('blocks,links,error,message',[
 (None,[],TypeError,'inputs must be lists or tuples'),
 ([[]]*9,None,TypeError,'inputs must be lists or tuples'),
 ([[]]*8,[],ValueError,'exactly nine blocks required'),
 ([[]]*10,[],ValueError,'exactly nine blocks required'),
 ([[]]*9,[None]*129,ValueError,'at most 128 links allowed'),
 ([[None]*9]+[[]]*8,[],ValueError,'blocks must contain at most eight entries'),
 ([None]+[[]]*8,[],ValueError,'blocks must contain at most eight entries'),
 ([[]]*9,[None],ValueError,'links must be pairs'),
 ([[]]*9,[(0,)],ValueError,'links must be pairs'),
 ([['']]+[[]]*8,[],ValueError,'entries must be strings of length 1 through 64'),
 ([['W'*65]]+[[]]*8,[],ValueError,'entries must be strings of length 1 through 64'),
 ([[None]]+[[]]*8,[],ValueError,'entries must be strings of length 1 through 64'),
 ([['x','y']]+[[]]*8,[(0,1),(0,1)],ValueError,'links must be unique'),
])
def test_errors(blocks,links,error,message):
    with pytest.raises(error) as exc:solve(blocks,links)
    assert str(exc.value)==message

@pytest.mark.parametrize('edge',[(True,1),(-1,1),(0,2),(0,0),(0,None),(1,1.0)])
def test_indices(edge):
    with pytest.raises(ValueError) as exc:solve([['x','y']]+[[]]*8,[edge])
    assert str(exc.value)=='links must contain nonbool valid distinct entry indices'
