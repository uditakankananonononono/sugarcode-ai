import copy
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.time_series_forecasting import forecast, STATUS_NOTE
class L(list): pass
class T(tuple): pass
class I(int): pass
@pytest.mark.parametrize('container',[L,T])
def test_outer_subclasses(container):
    with pytest.raises(ValueError,match='^history: list required$'):forecast(container([1,2,3]),1,1,1)
def test_history_scalar_subclass_nonfirst():
    with pytest.raises(ValueError,match=r'^history\[1\]: integer required$'):forecast([1,I(2),3],1,1,1)
@pytest.mark.parametrize('slot,name',[(0,'alpha_bps'),(1,'beta_bps'),(2,'horizon')])
def test_parameter_subclasses(slot,name):
    args=[1,1,1];args[slot]=I(1)
    with pytest.raises(ValueError,match='^'+name+': integer required$'):forecast([1,2,3],*args)
@pytest.mark.parametrize('container',[list,tuple])
def test_complete_fraction_contract_and_unchanged(container):
    history=container([10,12,16]);before=copy.deepcopy(history)
    result=forecast(history,5000,2500,2)
    assert result=={'level':F(15),'trend':F(9,4),'forecast':[F(69,4),F(39,2)],'mae':F(1),
                   'status_note':'PARTIAL: linear-trend smoothing of the supplied past only; no seasonality or turning points and no promise about the future'}
    assert result['status_note']==STATUS_NOTE and history==before
