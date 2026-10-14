from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.motion_design import design_motion as solve


def test_endpoint_midpoint_derivative_and_bound_oracle():
    r=solve(2,10,4,3)
    assert r['frames']==[
        {'time':0,'position':2,'velocity':0,'acceleration':0},
        {'time':2,'position':6,'velocity':F(15,4),'acceleration':0},
        {'time':4,'position':10,'velocity':0,'acceleration':0}]
    assert r['peak_speed']==F(15,4) and r['acceleration_bound']==3
    assert r['mode']=='quintic' and r['rendered'] is False


def test_quarter_point_independent_polynomial_integral_and_reverse():
    # Integral of normalized speed30*s²*(1-s)² gives ease.
    r=solve(0,1,1,5)
    assert r['frames'][1]=={'time':F(1,4),'position':F(53,512),
                            'velocity':F(135,128),'acceleration':F(45,8)}
    backwards=solve(1,0,1,5)
    for forward,back in zip(r['frames'],backwards['frames']):
        assert forward['position']+back['position']==1
        assert forward['velocity']==-back['velocity']
        assert forward['acceleration']==-back['acceleration']
        assert abs(forward['velocity'])<=r['peak_speed']
        assert abs(forward['acceleration'])<=r['acceleration_bound']


def test_static_reduced_motion_zero_distance_defaults_and_boundaries():
    import inspect
    assert inspect.signature(solve).parameters['samples'].default==17
    assert inspect.signature(solve).parameters['reduced_motion'].default is False
    r=solve(0,4,1,reduced_motion=True)
    assert r=={'frames':[{'time':0,'position':4,'velocity':0,'acceleration':0}],
              'peak_speed':0,'acceleration_bound':0,'mode':'static','rendered':False}
    assert all(f['position']==3 for f in solve(3,3,1,257)['frames'])
    assert len(solve(0,1,1,2)['frames'])==2
    for value in [2**32-1,F(2**32-1),F(1,2**32-1)]:
        assert solve(value,value,1)['frames'][0]['position']==value

@pytest.mark.parametrize('args,error,message',[
 ((0,1,1,True),ValueError,'samples must be a nonbool integer between 2 and 257'),
 ((0,1,1,1),ValueError,'samples must be a nonbool integer between 2 and 257'),
 ((0,1,1,258),ValueError,'samples must be a nonbool integer between 2 and 257'),
 ((0,1,1,17,0),TypeError,'reduced_motion must be bool'),
 ((True,1,1),TypeError,'values must be nonbool int or Fraction'),
 ((0,1,1.0),TypeError,'values must be nonbool int or Fraction'),
 ((0,1,0),ValueError,'duration must be positive'),
 ((0,1,-1),ValueError,'duration must be positive'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('value',[2**32,F(2**32),F(1,2**32)])
def test_next_bit(value):
    with pytest.raises(ValueError,match='^values must fit 32 bits$'):solve(value,0,1)


def test_duration_acceleration_scales_quadratically_not_linearly():
    r=solve(0,1,2,5)
    assert r['frames'][1]['acceleration']==F(45,32)
    assert r['frames'][1]['velocity']==F(135,256)

@pytest.mark.parametrize('samples',[3.0,'3',None])
def test_sample_type_declared_error(samples):
    with pytest.raises(ValueError) as exc:solve(0,1,1,samples)
    assert str(exc.value)=='samples must be a nonbool integer between 2 and 257'
