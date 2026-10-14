import pytest
from sugarcode.extra_doc.api_design import route_contract as solve


def test_endpoint_routing_required_keys_oracle():
    endpoints=[('GET','/x',[]),('POST','/x',['b','a'])]
    assert solve(endpoints,'POST','/x',['a'])=={'endpoint_index':1,'missing_keys':['b'],'accepted':False,'request_executed':False}
    assert solve(endpoints,'POST','/x',['a','b','extra'])['accepted'] is True
    assert solve(endpoints,'GET','/missing',[])['endpoint_index'] is None
    assert solve([('GET','/'+str(i),['W'*32]*1) for i in range(32)],'GET','/31',['W'*32]*16)['accepted'] is True
    assert solve([('GET','/'+'W'*63,[])],'GET','/'+'W'*63,[])['accepted'] is True

@pytest.mark.parametrize('args,error,message',[
 ((None,'GET','/',[]),TypeError,'inputs must be lists or tuples'),
 (([('GET','/',[])],'GET','/',None),TypeError,'inputs must be lists or tuples'),
 (([],'GET','/',[]),ValueError,'endpoint count must be 1..32 and at most 16 body keys allowed'),
 (([None]*33,'GET','/',[]),ValueError,'endpoint count must be 1..32 and at most 16 body keys allowed'),
 (([('GET','/',[])],'GET','/',[None]*17),ValueError,'endpoint count must be 1..32 and at most 16 body keys allowed'),
 (([('GET','/')],'GET','/',[]),ValueError,'endpoints must contain method path required keys triples'),
 (([('GET','/',[],0)],'GET','/',[]),ValueError,'endpoints must contain method path required keys triples'),
 (([('GET','/',[]),None],'GET','/',[]),ValueError,'endpoints must contain method path required keys triples'),
 (([('GET','/',None)],'GET','/',[]),ValueError,'at most 16 required keys per endpoint allowed'),
 (([('GET','/',['x']*17)],'GET','/',[]),ValueError,'at most 16 required keys per endpoint allowed'),
 (([('GET','/',['x','x'])],'GET','/',[]),ValueError,'required keys must be unique'),
 (([('GET','/',[])]*2,'GET','/',[]),ValueError,'endpoint routes must be unique'),
])
def test_shapes(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('bad',[None,True,'','W'*33])
def test_keys(bad):
    with pytest.raises(ValueError) as exc:solve([('GET','/',[])],'GET','/',[bad])
    assert str(exc.value)=='body keys must be strings of length 1 through 32'
    with pytest.raises(ValueError) as exc:solve([('GET','/',[bad])],'GET','/',[])
    assert str(exc.value)=='required keys must be strings of length 1 through 32'

@pytest.mark.parametrize('bad',[None,True,'get','X'])
def test_method(bad):
    with pytest.raises(ValueError) as exc:solve([('GET','/',[])],bad,'/',[])
    assert str(exc.value)=='method must be GET POST PUT or DELETE'

@pytest.mark.parametrize('bad',[None,True,'','x','/'+'W'*64])
def test_path(bad):
    with pytest.raises(ValueError) as exc:solve([('GET','/',[])],'GET',bad,[])
    assert str(exc.value)=='path must start with slash and have length 1 through 64'
