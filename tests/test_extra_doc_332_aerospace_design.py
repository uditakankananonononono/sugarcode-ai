from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.aerospace_design import thrust_concept as solve


def test_static_force_balance_and_cost_oracle():
    r=solve([[(1,2,1),(2,8,3)],[(1,0,1),(0,0,2)]],1,2)
    #00mass3/thrust2fail;01mass2/thrust2fail;10mass4/thrust8equalcost4;11mass3/thrust8cost5.
    assert r=={'option_indices':[1,0],'total_mass':4,'total_thrust':8,'thrust_surplus':0,
              'cost':4,'feasible_count':2,'flightworthiness_validated':False}
    assert solve([[(F(1,2),2,0)]],F(1,2),F(3,2))['thrust_surplus']==F(1,2)


def test_zero_components_ties_caps_and_input_bits():
    r=solve([[(0,0,0)]*4]*6,0,1)
    assert r['option_indices']==[0]*6 and r['feasible_count']==4096
    for v in [2**32-1,F(2**32-1),F(1,2**32-1)]:
        assert solve([[(v,v,0)]],0,1)['thrust_surplus']==0
    with pytest.raises(ValueError,match='^no concept meets static thrust requirement$'):solve([[(1,0,0)]],0,1)

@pytest.mark.parametrize('args,error,message',[
 ((None,0,1),TypeError,'components must be a list or tuple'),
 (([],0,1),ValueError,'category count must be between 1 and 6'),
 (([None]*7,0,1),ValueError,'category count must be between 1 and 6'),
 (([[]],0,1),ValueError,'each category must have between 1 and 4 options'),
 (([[None]*5],0,1),ValueError,'each category must have between 1 and 4 options'),
 (([[None]],0,1),ValueError,'options must contain mass thrust and cost'),
 (([[(0,0,0)]],True,1),TypeError,'values must be nonbool int or Fraction'),
 (([[(0,0,0)]],-1,1),ValueError,'payload must be nonnegative'),
 (([[(0,0,0)]],0,0),ValueError,'required_acceleration must be positive'),
 (([[(-1,0,0)]],0,1),ValueError,'mass thrust and cost must be nonnegative'),
 (([[(0,-1,0)]],0,1),ValueError,'mass thrust and cost must be nonnegative'),
 (([[(0,0,-1)]],0,1),ValueError,'mass thrust and cost must be nonnegative'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('v',[2**32,F(2**32),F(1,2**32)])
def test_next_bit(v):
    with pytest.raises(ValueError,match='^values must fit 32 bits$'):solve([[(v,0,0)]],0,1)
