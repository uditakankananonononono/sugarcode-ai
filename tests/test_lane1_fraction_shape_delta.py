import pytest
from sugarcode.extra_doc.mcmc1032 import propagate
from sugarcode.extra_doc.hmc1036 import integrate
from sugarcode.extra_doc.smc1037 import update as smc
from sugarcode.extra_doc.ekf1040 import update as ekf
from sugarcode.extra_doc.ukf1041 import transform
class I(int):pass
@pytest.mark.parametrize('bad',[(1,2,3),(1,),(),(1,2.0),(1.0,2),(1,True),(True,2),(1,I(2)),(I(1),2)])
def test_shape(bad):
    for call,message in [(lambda:propagate(bad,(1,2),0,1),'probabilities must be exact integer fractions with 1<=num<den<=100'),(lambda:propagate((1,2),bad,0,1),'probabilities must be exact integer fractions with 1<=num<den<=100'),(lambda:integrate(0,0,bad,1),'step must be an exact integer fraction with 1<=num<=den<=100')]:
        with pytest.raises(ValueError) as exc:call()
        assert str(exc.value)==message
@pytest.mark.parametrize('bad',[101,True,1.5,I(1)])
def test_hmc_momentum_refusal(bad):
    with pytest.raises(ValueError) as exc:integrate(0,bad,(1,2),1)
    assert str(exc.value)=='coordinates must be exact integers in -100..100'
def test_smc():
    assert len(smc([1]*50,[1]*50)['weights'])==50
    with pytest.raises(ValueError) as exc:smc([1]*51,[1]*51)
    assert str(exc.value)=='prior must be an exact list with 1..50 entries'
    with pytest.raises(ValueError) as exc:smc([1],[1,2])
    assert str(exc.value)=='likelihood must be an exact list matching prior count'
@pytest.mark.parametrize('bad',[True,1.5,I(1),-101,101])
def test_ekf(bad):
    for call in (lambda:ekf(0,1,bad,1),lambda:ekf(bad,1,0,1)):
        with pytest.raises(ValueError) as exc:call()
        assert str(exc.value)=='mean and measurement must be integers in -100..100'
def test_b():
    for m in (-100,100):
        assert ekf(m,100,m,100)['claim']=='PARTIAL'
        assert transform(m,100)['claim']=='PARTIAL'
    for call,message in [(lambda:ekf(0,101,0,1),'variance must be an integer in 0..100'),(lambda:ekf(0,1,0,101),'noise must be an integer in 1..100'),(lambda:transform(0,101),'spread must be an integer in 1..100')]:
        with pytest.raises(ValueError) as exc:call()
        assert str(exc.value)==message
