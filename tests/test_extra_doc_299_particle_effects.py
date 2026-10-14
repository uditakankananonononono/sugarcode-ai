from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.particle_effects import ballistic_particles as solve


def test_closed_form_positions_and_derivative_oracle():
    r=solve([[0,0,0],[2,-1,4]],[[1,2,3],[-1,0,1]],[0,0,-2],[0,F(1,2),2])
    assert r['frames'][0]['positions']==[[0,0,0],[2,-1,4]]
    assert r['frames'][1]['positions']==[[F(1,2),1,F(5,4)],[F(3,2),-1,F(17,4)]]
    assert r['frames'][2]['positions']==[[2,4,2],[0,-1,2]]
    assert r['frames'][2]['velocities']==[[1,2,-1],[-1,0,-3]]
    assert r['particle_count']==2 and r['rendered'] is False
    # For constant acceleration, central difference in position is exact velocity.
    r=solve([[2,3,4]],[[1,-2,3]],[2,4,-6],[1,2,3])
    for i in range(3):assert (r['frames'][2]['positions'][0][i]-r['frames'][0]['positions'][0][i])/2==r['frames'][1]['velocities'][0][i]


def test_max_shape_single_time_and_scalar_edges():
    r=solve([[0]*3]*32,[[0]*3]*32,[0]*3,list(range(64)))
    assert len(r['frames'])==64 and len(r['frames'][0]['positions'])==32
    for v in [2**32-1,F(2**32-1),F(1,2**32-1)]:
        assert solve([[v,0,0]],[[0]*3],[0]*3,[0])['frames'][0]['positions'][0][0]==v

@pytest.mark.parametrize('args,error,message',[
 ((None,[],[],[]),TypeError,'inputs must be lists or tuples'),
 (([],[],[0]*3,[0]),ValueError,'particle count must be between 1 and 32'),
 (([None]*33,[],[0]*3,[0]),ValueError,'particle count must be between 1 and 32'),
 (([[0]*3],[[0]*3],[0]*3,[]),ValueError,'time count must be between 1 and 64'),
 (([[0]*3],[[0]*3],[0]*3,[None]*65),ValueError,'time count must be between 1 and 64'),
 (([[0]*3],[],[0]*3,[0]),ValueError,'velocity count must match particles'),
 (([[0,0]],[[0]*3],[0]*3,[0]),ValueError,'vectors must have three coordinates'),
 (([[0]*3],[[0]*3],[0,0],[0]),ValueError,'vectors must have three coordinates'),
 (([[True,0,0]],[[0]*3],[0]*3,[0]),TypeError,'values must be nonbool int or Fraction'),
 (([[0]*3],[[0]*3],[0]*3,[-1]),ValueError,'times must be nonnegative'),
 (([[0]*3],[[0]*3],[0]*3,[0,0]),ValueError,'times must be strictly increasing'),
 (([[0]*3],[[0]*3],[0]*3,[1,0]),ValueError,'times must be strictly increasing'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('v',[2**32,F(2**32),F(1,2**32)])
def test_next_bit(v):
    with pytest.raises(ValueError,match='^values must fit 32 bits$'):solve([[v,0,0]],[[0]*3],[0]*3,[0])
