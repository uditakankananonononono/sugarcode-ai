import pytest
from sugarcode.extra_doc.load_balancing import dispatch_requests as solve

def test_projected_normalized_dispatch():
    assert solve([0,2,0],[1,2,10],[True,True,False],[2,1,3])=={'server_indices':[0,1,1],'final_loads':[2,6,0],'normalized_loads':[2,3,0],'traffic_routed':False}
    assert solve([0,0],[1,1],[True,True],[1,1])['server_indices']==[0,1]
    assert solve([0],[1000],[True],[0])['server_indices']==[0]
    assert len(solve([2**32-1]*16,[1000]*16,[True]*16,[2**32-1]*64)['server_indices'])==64
    assert solve([0],[1],[True],[])['final_loads']==[0]

@pytest.mark.parametrize('args,error,message',[
 ((None,[],[],[]),TypeError,'inputs must be lists or tuples'),
 (([],[],[],[]),ValueError,'server count must be 1..16 and at most 64 requests allowed'),
 (([None]*17,[],[],[]),ValueError,'server count must be 1..16 and at most 64 requests allowed'),
 (([0],[1],[True],[None]*65),ValueError,'server count must be 1..16 and at most 64 requests allowed'),
 (([0],[],[True],[]),ValueError,'server shapes must agree'),
 (([0],[1],[],[]),ValueError,'server shapes must agree'),
 (([0],[1],[1],[]),TypeError,'availability flags must be bool'),
 (([0],[1],[False],[]),ValueError,'at least one server must be available'),
])
def test_shapes(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('slot',[0,3])
@pytest.mark.parametrize('bad',[True,-1,2**32,None,1.0])
def test_weights(slot,bad):
    args=[[0],[1],[True],[]];args[slot]=[bad]
    with pytest.raises(ValueError) as exc:solve(*args)
    assert str(exc.value)=='loads and requests must be nonbool integers zero through 4294967295'

@pytest.mark.parametrize('bad',[True,0,1001,None,1.0])
def test_capacity(bad):
    with pytest.raises(ValueError) as exc:solve([0],[bad],[True],[])
    assert str(exc.value)=='capacities must be nonbool integers one through 1000'
