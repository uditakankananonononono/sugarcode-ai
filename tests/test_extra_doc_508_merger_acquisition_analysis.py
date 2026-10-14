from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.merger_acquisition_analysis import acquisition_value as solve


def test_end_period_discount_and_break_even_oracle():
    assert solve(100,110,10,[30,-9],5000)=={'discounted_synergies':[20,-4],
      'synergy_present_value':16,'break_even_price':106,'acquisition_npv':-4,
      'positive_npv':False,'transaction_performed':False}
    assert solve(0,0,0,[0],0)['positive_npv'] is False
    assert solve(1,0,0,[0],10000)['positive_npv'] is True
    assert solve(2**32-1,2**32-1,2**32-1,[2**32-1]*24,0)['synergy_present_value']==24*(2**32-1)
    assert solve(0,0,0,[-(2**32-1)],0)['synergy_present_value']==-(2**32-1)

@pytest.mark.parametrize('synergies,error,message',[
 (None,TypeError,'synergies must be a list or tuple'),([],ValueError,'synergy period count must be between 1 and 24'),
 ([None]*25,ValueError,'synergy period count must be between 1 and 24'),
])
def test_shapes(synergies,error,message):
    with pytest.raises(error) as exc:solve(0,0,0,synergies,0)
    assert str(exc.value)==message

@pytest.mark.parametrize('slot',range(3))
@pytest.mark.parametrize('bad',[True,-1,2**32,None,1.0])
def test_values(slot,bad):
    args=[0,0,0,[0],0];args[slot]=bad
    with pytest.raises(ValueError) as exc:solve(*args)
    assert str(exc.value)=='values prices and costs must be nonbool integers zero through 4294967295'

@pytest.mark.parametrize('bad',[True,2**32,-(2**32),None,1.0])
def test_cashflows(bad):
    with pytest.raises(ValueError) as exc:solve(0,0,0,[0,bad],0)
    assert str(exc.value)=='synergies must be nonbool 32-bit magnitude signed integers'

@pytest.mark.parametrize('bad',[True,-1,10001,None,1.0])
def test_discount(bad):
    with pytest.raises(ValueError) as exc:solve(0,0,0,[0],bad)
    assert str(exc.value)=='discount must be nonbool integer zero through 10000 basis points'
