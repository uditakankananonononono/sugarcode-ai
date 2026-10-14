from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.automotive_design import vehicle_layout as solve


def test_static_moment_and_finite_cost_oracle():
    # Two components each mass2 at front/rear; caps2/2require opposite choices.
    r=solve([[(2,0,1),(2,4,3)],[(2,0,2),(2,4,5)]],4,2,2)
    # cost6 for front/rear,cost5 for rear/front.
    assert r=={'option_indices':[1,0],'total_mass':4,'front_load':2,'rear_load':2,
              'cost':5,'feasible_count':2,'roadworthiness_validated':False}
    r=solve([[(3,1,0)]],4,3,3)
    assert r['rear_load']==F(3,4) and r['front_load']==F(9,4)


def test_zero_mass_equal_cap_tie_and_max_shape():
    assert solve([[(0,0,0),(0,1,0)]],1,0,0)['option_indices']==[0]
    r=solve([[(1,0,0)]*4]*6,1,6,0)
    assert r['feasible_count']==4096 and r['front_load']==6
    for v in [2**32-1,F(2**32-1),F(1,2**32-1)]:
        assert solve([[(v,0,0)]],1,v,0)['total_mass']==v
    with pytest.raises(ValueError,match='^no layout satisfies axle caps$'):solve([[(1,0,0)]],1,0,0)

@pytest.mark.parametrize('args,error,message',[
 ((None,1,1,1),TypeError,'components must be a list or tuple'),
 (([],1,1,1),ValueError,'component count must be between 1 and 6'),
 (([None]*7,1,1,1),ValueError,'component count must be between 1 and 6'),
 (([[]],1,1,1),ValueError,'each component must have between 1 and 4 options'),
 (([[None]*5],1,1,1),ValueError,'each component must have between 1 and 4 options'),
 (([[None]],1,1,1),ValueError,'options must contain mass position and cost'),
 (([[(1,0,0)]],True,1,1),TypeError,'values must be nonbool int or Fraction'),
 (([[(1,0,0)]],0,1,1),ValueError,'wheelbase must be positive'),
 (([[(1,0,0)]],1,-1,1),ValueError,'axle caps must be nonnegative'),
 (([[(-1,0,0)]],1,1,1),ValueError,'mass cost and positions must be nonnegative and positions within wheelbase'),
 (([[(1,2,0)]],1,1,1),ValueError,'mass cost and positions must be nonnegative and positions within wheelbase'),
 (([[(1,0,-1)]],1,1,1),ValueError,'mass cost and positions must be nonnegative and positions within wheelbase'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('v',[2**32,F(2**32),F(1,2**32)])
def test_next_bit(v):
    with pytest.raises(ValueError,match='^values must fit 32 bits$'):solve([[(v,0,0)]],1,1,1)
