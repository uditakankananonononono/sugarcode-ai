from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.rendering_optimization import allocate_render_modes as solve


def test_four_allocation_quality_time_oracle():
    # times/qualities: (2,2),(5,8),(4,6),(7,12). Budget5 picks(5,8).
    r=solve([[(1,1),(3,5)],[(1,1),(4,7)]],5)
    assert r=={'mode_indices':[0,1],'total_quality':8,'total_time':5,'budget_slack':0,
              'candidate_count':4,'feasible_count':3,'renderer_executed':False}


def test_quality_tie_prefers_lower_time_then_supplied_order():
    assert solve([[(3,5),(2,5),(2,5)]],3)['mode_indices']==[1]
    r=solve([[(F(1,2),2)],[(F(1,3),3)]],1)
    assert r['total_time']==F(5,6) and r['budget_slack']==F(1,6)
    assert solve([[(0,0)]],0)['feasible_count']==1
    r=solve([[(0,0)]*4]*6,0)
    assert r['candidate_count']==4096 and r['mode_indices']==[0]*6
    for v in [2**32-1,F(2**32-1),F(1,2**32-1)]:
        assert solve([[(v,v)]],v)['total_quality']==v

@pytest.mark.parametrize('args,error,message',[
 ((None,0),TypeError,'components must be a list or tuple'),
 (([],0),ValueError,'component count must be between 1 and 6'),
 (([None]*7,0),ValueError,'component count must be between 1 and 6'),
 (([[]],0),ValueError,'each component must have between 1 and 4 modes'),
 (([[None]*5],0),ValueError,'each component must have between 1 and 4 modes'),
 (([[None]],0),ValueError,'modes must contain time and quality'),
 (([[(0,0,0)]],0),ValueError,'modes must contain time and quality'),
 (([[(0,0)]],True),TypeError,'values must be nonbool int or Fraction'),
 (([[(0,0)]],-1),ValueError,'time budget must be nonnegative'),
 (([[(-1,0)]],0),ValueError,'mode time and quality must be nonnegative'),
 (([[(0,-1)]],0),ValueError,'mode time and quality must be nonnegative'),
 (([[(1,1)]],0),ValueError,'no render allocation fits time budget'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('v',[2**32,F(2**32),F(1,2**32)])
def test_next_bit(v):
    with pytest.raises(ValueError,match='^values must fit 32 bits$'):solve([[(0,v)]],0)
