import pytest
from sugarcode.extra_doc.pain_point_discovery import discover_pain as solve


def test_explicit_priority_and_zero_impact_oracle():
    assert solve([(5,10,20),(10,10,10),(5,10,20),(0,100,0),(100,0,0),(100,100,100)])=={
      'priorities':[4000,9000,4000,0,0,0],'unmet_need_indices':[1,0,2],
      'zero_priority_indices':[3,4,5],'needs_validated':False}
    assert solve([(100,100,0)]*64)['priorities']==[1000000]*64

@pytest.mark.parametrize('needs,error,message',[
 (None,TypeError,'needs must be a list or tuple'),
 ([],ValueError,'need count must be between 1 and 64'),
 ([None]*65,ValueError,'need count must be between 1 and 64'),
 ([None],ValueError,'needs must contain severity frequency satisfaction triples'),
 ([(1,2)],ValueError,'needs must contain severity frequency satisfaction triples'),
 ([(1,2,3,4)],ValueError,'needs must contain severity frequency satisfaction triples'),
])
def test_shapes(needs,error,message):
    with pytest.raises(error) as exc:solve(needs)
    assert str(exc.value)==message

@pytest.mark.parametrize('bad',[True,-1,101,None,1.0])
@pytest.mark.parametrize('slot',[0,1,2])
def test_scalars(bad,slot):
    row=[1,1,1];row[slot]=bad
    with pytest.raises(ValueError) as exc:solve([row])
    assert str(exc.value)=='ratings must be nonbool integers zero through 100'
