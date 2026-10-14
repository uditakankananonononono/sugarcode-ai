from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.lighting_design import select_lights as solve


def test_two_light_four_subset_oracle():
    # illumination: empty(0,0),first(4,1),second(1,4),both(5,5).
    # target(4,2): errors20,1,13,10. First is global optimum.
    r=solve([4,4],[[1,4],[4,1]],[4,2],2)
    assert r=={'selected_lights':[0],'illumination':[4,1],'squared_error':1,
              'feasible_subset_count':4,'mood_validated':False}
    assert solve([4,4],[[1,4],[4,1]],[5,5],2)['selected_lights']==[0,1]
    assert solve([4,4],[[1,4],[4,1]],[5,5],1)['selected_lights']==[0]


def test_empty_selection_tie_fractional_boundaries_and_max_shape():
    assert solve([0,0],[[1],[1]],[0],2)['selected_lights']==[]
    r=solve([1],[[2]],[F(1,2)],1)
    assert r['illumination']==[F(1,2)] and r['squared_error']==0
    assert solve([1],[[1]],[1],0)['feasible_subset_count']==1
    r=solve([0]*12,[[1]*8]*12,[0]*8,12)
    assert r['feasible_subset_count']==4096
    for value in [2**32-1,F(2**32-1),F(1,2**32-1)]:
        assert solve([value],[[1]],[value],1)['squared_error']==0

@pytest.mark.parametrize('args,error,message',[
 ((None,[],[],0),TypeError,'inputs must be lists or tuples'),
 (([],[],[0],0),ValueError,'light count must be between 1 and 12'),
 (([None]*13,[],[0],0),ValueError,'light count must be between 1 and 12'),
 (([1],[],[],0),ValueError,'sample count must be between 1 and 8'),
 (([1],[],[None]*9,0),ValueError,'sample count must be between 1 and 8'),
 (([1],[[1]],[0],True),ValueError,'max_lights must be a nonbool integer between zero and light count'),
 (([1],[[1]],[0],2),ValueError,'max_lights must be a nonbool integer between zero and light count'),
 (([1],[],[0],0),ValueError,'distance matrix must match lights and samples'),
 (([1],['1'],[0],0),ValueError,'distance matrix must match lights and samples'),
 (([True],[[1]],[0],0),TypeError,'values must be nonbool int or Fraction'),
 (([-1],[[1]],[0],0),ValueError,'intensities and targets must be nonnegative'),
 (([1],[[1]],[-1],0),ValueError,'intensities and targets must be nonnegative'),
 (([1],[[0]],[0],0),ValueError,'squared distances must be positive'),
 (([1],[[-1]],[0],0),ValueError,'squared distances must be positive'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('value',[2**32,F(2**32),F(1,2**32)])
def test_next_bit(value):
    with pytest.raises(ValueError,match='^values must fit 32 bits$'):solve([value],[[1]],[0],1)


def test_negative_light_budget_refused():
    with pytest.raises(ValueError) as exc:solve([1],[[1]],[0],-1)
    assert str(exc.value)=='max_lights must be a nonbool integer between zero and light count'
