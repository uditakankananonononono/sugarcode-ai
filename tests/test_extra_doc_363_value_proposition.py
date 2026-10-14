import pytest
from sugarcode.extra_doc.value_proposition import design_offer as solve


def test_cover_once_explicit_offer_oracle():
    assert solve([2,2,3],[[0,1],[1,2],[0,2]],[5,10,4],4)=={
      'feature_indices':[0,1],'covered_needs':[0,1,2],'importance':19,'cost':4,'customer_response_validated':False}
    assert solve([5,1],[[0],[0]],[7],5)['feature_indices']==[1]
    assert solve([1,1,2],[[0],[1],[0,1]],[3,4],2)['feature_indices']==[2]
    assert solve([1]*4,[[0],[1],[0],[1]],[3,4],2)['feature_indices']==[0,1]
    assert solve([1],[[]],[1],0)['feature_indices']==[]


def test_all_caps_and_boundary_scalars():
    assert solve([0]*12,[list(range(16))]*12,[1000000]*16,1000000)['importance']==16000000
    assert solve([1000000],[[0]],[1000000],1000000)['cost']==1000000

@pytest.mark.parametrize('args,error,message',[
 ((None,[],[],0),TypeError,'inputs must be lists or tuples'),
 (([],[],[1],0),ValueError,'feature count must be 1..12 and need count 1..16'),
 (([0]*13,[],[1],0),ValueError,'feature count must be 1..12 and need count 1..16'),
 (([0],[[]],[],0),ValueError,'feature count must be 1..12 and need count 1..16'),
 (([0],[[]],[0]*17,0),ValueError,'feature count must be 1..12 and need count 1..16'),
 (([0],[],[1],0),ValueError,'coverage rows must match features and contain at most 16 indices'),
 (([0],[[0]*17],[1],0),ValueError,'coverage rows must match features and contain at most 16 indices'),
 (([0],[[0,0]],[1],0),ValueError,'need indices must be unique'),
])
def test_shape_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('bad',[True,-1,1000001,None,1.0])
@pytest.mark.parametrize('slot',[0,2,3])
def test_scalars(bad,slot):
    args=[[0],[[0]],[1],0];args[slot]=bad if slot==3 else [bad]
    with pytest.raises(ValueError) as exc:solve(*args)
    assert str(exc.value)=='costs importance and budget must be nonbool integers zero through 1000000'

@pytest.mark.parametrize('bad',[True,-1,1,None])
def test_indices(bad):
    with pytest.raises(ValueError) as exc:solve([0],[[bad]],[1],0)
    assert str(exc.value)=='need indices must be nonbool valid indices'
