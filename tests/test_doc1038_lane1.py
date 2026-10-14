from fractions import Fraction
import itertools
import pytest
from sugarcode.extra_doc.particle1038 import resample


def test_independent_interval_oracle():
    for weights in itertools.product((0,1,3),repeat=3):
        if not sum(weights):continue
        for count in range(1,8):
            for u in (Fraction(0),Fraction(1,2),Fraction(3,4)):
                expected=[];total=sum(weights)
                for j in range(count):
                    point=(j+u)*total/count
                    for i in range(3):
                        if sum(weights[:i])<=point<sum(weights[:i+1]):expected.append(i);break
                got=resample(list(weights),count,(u.numerator,u.denominator))
                assert got['indexes']==expected
                assert got['claim']=='PARTIAL' and got['filter_validated'] is False

class L(list):pass
class I(int):pass
class T(tuple):pass
@pytest.mark.parametrize('args,message',[
 ( (L([1]),1,(0,1)),'weights must be an exact list with 1..50 entries'),
 (([],1,(0,1)),'weights must be an exact list with 1..50 entries'),
 *[(([x],1,(0,1)),'weights must be integers in 0..100 with positive sum') for x in (True,I(1),-1,101,0)],
 *[(([1],x,(0,1)),'count must be an integer in 1..50') for x in (True,I(1),0,51)],
 *[(([1],1,x),'offset must be an exact integer fraction with 0<=num<den<=100') for x in (T((0,1)),(True,2),(I(0),2),(-1,2),(2,2),(0,101))],
])
def test_invalid(args,message):
    with pytest.raises(ValueError) as exc:resample(*args)
    assert str(exc.value)==message


def test_zero_weight_exact_boundary_and_caps():
    assert resample([0,1,1],2,(0,1))['indexes']==[1,2]
    assert resample([100]*50,50,(0,100))['indexes']==list(range(50))
