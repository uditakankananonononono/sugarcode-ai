import copy
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.anomaly_detection import detect, STATUS_NOTE
class L(list): pass
class T(tuple): pass
class I(int): pass
@pytest.mark.parametrize('container',[L,T])
def test_outer_subclasses(container):
    with pytest.raises(ValueError,match='^values: list required$'):detect(container([1,2,3,4]))
def test_scalar_subclasses_nonfirst():
    with pytest.raises(ValueError,match=r'^values\[2\]: integer required$'):detect([1,2,I(3),4])
    with pytest.raises(ValueError,match='^k_tenths: integer required$'):detect([1,2,3,4],I(15))
@pytest.mark.parametrize('container',[list,tuple])
def test_full_default_contract_status_and_unchanged(container):
    values=container([16,0,4,8,-8]);before=copy.deepcopy(values)
    assert detect(values,10)=={'q1':F(0),'q3':F(8),'iqr':F(8),'lower':F(-8),'upper':F(16),
                              'outliers':[],'status_note':'PARTIAL: interquartile-range fences over the supplied list only; an outlier is unusual in this list, not proof of an error or a cause'}
    assert detect(values)['status_note']==STATUS_NOTE
    assert detect(values)==detect(values,15) and values==before
