from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.sound_installation_design import spatial_gains as solve


def test_inverse_square_normalized_gain_oracle_and_floor():
    r=solve([[0,0,0],[3,0,0]],[[1,0,0],[0,0,0],[F(3,2),0,0]])
    assert r['squared_distances']==[[1,4],[0,9],[F(9,4),F(9,4)]]
    assert r['gains']==[[F(4,5),F(1,5)],[F(9,10),F(1,10)],[F(1,2),F(1,2)]]
    assert r['immersion_validated'] is False
    assert solve([[0,0,0],[3,0,0]],[[1,0,0]],4)['gains']==[[F(1,2),F(1,2)]]


def test_translation_invariance_max_shape_and_scalar_edges():
    a=solve([[0,1,2],[3,4,5]],[[2,1,0]])
    b=solve([[10,11,12],[13,14,15]],[[12,11,10]])
    assert a==b
    r=solve([[0]*3]*8,[[0]*3]*32)
    assert len(r['gains'])==32 and all(row==[F(1,8)]*8 for row in r['gains'])
    for value in [2**32-1,F(2**32-1),F(1,2**32-1)]:
        assert solve([[value,0,0]],[[0,0,0]])['gains']==[[1]]

@pytest.mark.parametrize('args,error,message',[
 ((None,[]),TypeError,'speakers and listeners must be lists or tuples'),
 (([],[[0]*3]),ValueError,'speaker count must be between 1 and 8'),
 (([None]*9,[[0]*3]),ValueError,'speaker count must be between 1 and 8'),
 (([[0]*3],[]),ValueError,'listener count must be between 1 and 32'),
 (([[0]*3],[None]*33),ValueError,'listener count must be between 1 and 32'),
 (([[0,0]],[[0]*3]),ValueError,'positions must have three coordinates'),
 (([[True,0,0]],[[0]*3]),TypeError,'values must be nonbool int or Fraction'),
 (([[0]*3],[[0]*3],0),ValueError,'distance_floor must be positive'),
 (([[0]*3],[[0]*3],-1),ValueError,'distance_floor must be positive'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('value',[2**32,F(2**32),F(1,2**32)])
def test_next_bit(value):
    with pytest.raises(ValueError,match='^values must fit 32 bits$'):solve([[value,0,0]],[[0]*3])


def test_listener_set_and_position_range_declared_errors():
    with pytest.raises(TypeError) as exc:solve([[0,0,0]],{(0,0,0)})
    assert str(exc.value)=='speakers and listeners must be lists or tuples'
    with pytest.raises(ValueError) as exc:solve([range(3)],[[0,0,0]])
    assert str(exc.value)=='positions must have three coordinates'
