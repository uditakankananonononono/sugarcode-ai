from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.system_architecture_design import architecture_reliability as solve


def test_series_parallel_independent_reliability_oracle():
    assert solve([5000,5000,8000],[[0,1],[2]])=={'group_availability':[F(3,4),F(4,5)],
      'system_availability':F(3,5),'architecture_deployed':False}
    assert solve([0,10000],[[0,1]])['system_availability']==1
    assert solve([0],[[0]])['system_availability']==0
    assert solve([10000]*16,[[i] for i in range(16)])['system_availability']==1

@pytest.mark.parametrize('args,error,message',[
 ((None,[]),TypeError,'inputs must be lists or tuples'),(([1],None),TypeError,'inputs must be lists or tuples'),
 (([],[[0]]),ValueError,'component and group counts must be between 1 and 16'),
 (([0]*17,[[0]]),ValueError,'component and group counts must be between 1 and 16'),
 (([0],[]),ValueError,'component and group counts must be between 1 and 16'),
 (([0],[None]*17),ValueError,'component and group counts must be between 1 and 16'),
 (([0],[[]]),ValueError,'groups must contain 1 through 16 indices'),
 (([0],[[0],None]),ValueError,'groups must contain 1 through 16 indices'),
 (([0],[[None]*17]),ValueError,'groups must contain 1 through 16 indices'),
 (([0],[[0],[0]]),ValueError,'component indices must be globally unique'),
])
def test_shapes(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('bad',[True,-1,10001,None,1.0])
def test_availability(bad):
    with pytest.raises(ValueError) as exc:solve([0,bad],[[0]])
    assert str(exc.value)=='availability must be nonbool integers zero through 10000'

@pytest.mark.parametrize('bad',[True,-1,1,None,'0'])
def test_indices(bad):
    with pytest.raises(ValueError) as exc:solve([0],[[bad]])
    assert str(exc.value)=='groups must contain nonbool valid component indices'
