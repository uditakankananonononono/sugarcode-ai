from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.marine_design import box_hull as solve


def test_archimedes_volume_waterline_and_reserve_oracle():
    r=solve(4,2,2,8000,1000,F(1,2))
    assert r=={'displaced_volume':8,'draft':1,'freeboard':1,'reserve_mass':4000,
              'freeboard_requirement_met':True,'seaworthiness_validated':False}
    assert r['draft']*4*2*1000==8000
    assert solve(4,2,2,12000,1000,F(1,2))['reserve_mass']==0
    r=solve(4,2,2,12001,1000,F(1,2))
    assert r['reserve_mass']==-1 and r['freeboard_requirement_met'] is False


def test_zero_mass_density_default_and_sinking_not_hidden():
    import inspect
    assert inspect.signature(solve).parameters['water_density'].default==1000
    assert inspect.signature(solve).parameters['minimum_freeboard'].default==0
    assert solve(1,1,1,0)['freeboard']==1
    assert solve(1,1,1,2000)['freeboard']==-1
    assert solve(1,1,1,0,1,1)['freeboard_requirement_met'] is True
    for value in [2**32-1,F(2**32-1),F(1,2**32-1)]:
        assert solve(1,1,1,value,1)['draft']==value

@pytest.mark.parametrize('args,error,message',[
 ((True,1,1,0),TypeError,'values must be nonbool int or Fraction'),
 ((0,1,1,0),ValueError,'hull dimensions must be positive'),
 ((1,-1,1,0),ValueError,'hull dimensions must be positive'),
 ((1,1,0,0),ValueError,'hull dimensions must be positive'),
 ((1,1,1,-1),ValueError,'mass must be nonnegative'),
 ((1,1,1,0,0),ValueError,'water_density must be positive'),
 ((1,1,1,0,1,-1),ValueError,'minimum_freeboard must be between zero and hull depth'),
 ((1,1,1,0,1,2),ValueError,'minimum_freeboard must be between zero and hull depth'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('value',[2**32,F(2**32),F(1,2**32)])
def test_next_bit(value):
    with pytest.raises(ValueError,match='^values must fit 32 bits$'):solve(value,1,1,0)
