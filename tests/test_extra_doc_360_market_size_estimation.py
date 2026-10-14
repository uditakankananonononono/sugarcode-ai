from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.market_size_estimation import market_funnel as solve


def test_explicit_segment_funnel_and_total_oracle():
    r=solve([(100,20,F(1,2),F(1,4)),(50,10,F(1,5),F(1,2))])
    assert r=={'segments':[{'tam':2000,'sam':1000,'som':250},{'tam':500,'sam':100,'som':50}],
              'totals':{'tam':2500,'sam':1100,'som':300},'forecast_validated':False}
    assert all(row['som']<=row['sam']<=row['tam'] for row in r['segments'])


def test_zero_full_fractions_caps_and_scalar_boundaries():
    assert solve([(0,0,0,1)])['totals']=={'tam':0,'sam':0,'som':0}
    assert solve([(1,1,1,1)]*64)['totals']['som']==64
    for value in [2**32-1,F(2**32-1),F(1,2**32-1)]:
        assert solve([(1,value,1,1)])['totals']['tam']==value
    assert solve([(2**32-1,1,1,1)])['totals']['som']==2**32-1

@pytest.mark.parametrize('args,error,message',[
 ((None,),TypeError,'segments must be a list or tuple'),
 (([],),ValueError,'segment count must be between 1 and 64'),
 (([None]*65,),ValueError,'segment count must be between 1 and 64'),
 (([None],),ValueError,'segments must contain count annual_spend serviceable obtainable'),
 (([(True,0,0,0)],),ValueError,'customer counts must be nonbool integers zero through 4294967295'),
 (([(-1,0,0,0)],),ValueError,'customer counts must be nonbool integers zero through 4294967295'),
 (([(2**32,0,0,0)],),ValueError,'customer counts must be nonbool integers zero through 4294967295'),
 (([(1,True,0,0)],),TypeError,'values must be nonbool int or Fraction'),
 (([(1,-1,0,0)],),ValueError,'annual spend must be nonnegative'),
 (([(1,1,-1,0)],),ValueError,'fractions must be between zero and one'),
 (([(1,1,2,0)],),ValueError,'fractions must be between zero and one'),
 (([(1,1,0,-1)],),ValueError,'fractions must be between zero and one'),
 (([(1,1,0,2)],),ValueError,'fractions must be between zero and one'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('value',[2**32,F(2**32),F(1,2**32)])
def test_next_bit(value):
    with pytest.raises(ValueError,match='^values must fit 32 bits$'):solve([(1,value,0,0)])
