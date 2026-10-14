import pytest
from sugarcode.extra_doc.mle1030 import estimate
from sugarcode.extra_doc.em1031 import step
from sugarcode.extra_doc.mcmc1032 import propagate
from sugarcode.extra_doc.gibbs1034 import sweep
from sugarcode.extra_doc.metropolis1035 import decide
from sugarcode.extra_doc.hmc1036 import integrate
from sugarcode.extra_doc.particle1038 import resample

class I(int):pass

@pytest.mark.parametrize('bad',[(1,2,3),(1,),(),(1,2.0),(1.0,2),(1,True),(True,2),(1,I(2)),(I(1),2)])
def test_fraction_exact_shape_both_element_types(bad):
    # Invalid parameters must fail as ValueError, never argument/unpack/index errors.
    calls=[
        (lambda:estimate(0,1,[bad]),'grid entries must be integer fraction tuples with 0<=num<=den<=100 and den>=1'),
        (lambda:step([0],bad,(1,2),(1,2)),'parameters must be exact integer fraction tuples with 1<=num<den<=100'),
        (lambda:step([0],(1,2),bad,(1,2)),'parameters must be exact integer fraction tuples with 1<=num<den<=100'),
        (lambda:step([0],(1,2),(1,2),bad),'parameters must be exact integer fraction tuples with 1<=num<den<=100'),
        (lambda:propagate(bad,(1,2),0,1),'probabilities must be exact integer fractions with 1<=num<den<=100'),
        (lambda:propagate((1,2),bad,0,1),'probabilities must be exact integer fractions with 1<=num<den<=100'),
        (lambda:sweep([[1,1],[1,1]],(0,0),(bad,(0,1))),'draws must be exact integer fractions with 0<=num<den<=100'),
        (lambda:sweep([[1,1],[1,1]],(0,0),((0,1),bad)),'draws must be exact integer fractions with 0<=num<den<=100'),
        (lambda:decide(1,1,1,1,bad),'draw must be an exact integer fraction with 0<=num<den<=100'),
        (lambda:integrate(0,0,bad,1),'step must be an exact integer fraction with 1<=num<=den<=100'),
        (lambda:resample([1],1,bad),'offset must be an exact integer fraction with 0<=num<den<=100'),
    ]
    for call,message in calls:
        with pytest.raises(ValueError) as exc:call()
        assert str(exc.value)==message

from sugarcode.extra_doc.smc1037 import update as smc
from sugarcode.extra_doc.kalman1039 import update as kalman
from sugarcode.extra_doc.ekf1040 import update as ekf
from sugarcode.extra_doc.ukf1041 import transform


@pytest.mark.parametrize('bad',[101,True,1.5,I(1)])
def test_hmc_momentum_refusal(bad):
    with pytest.raises(ValueError) as exc:integrate(0,bad,(1,2),1)
    assert str(exc.value)=='coordinates must be exact integers in -100..100'


def test_smc_particle_both_caps_and_longer_likelihood():
    assert len(smc([1]*50,[1]*50)['weights'])==50
    with pytest.raises(ValueError) as exc:smc([1]*51,[1]*51)
    assert str(exc.value)=='prior must be an exact list with 1..50 entries'
    with pytest.raises(ValueError) as exc:smc([1],[1,2])
    assert str(exc.value)=='likelihood must be an exact list matching prior count'
    assert len(resample([1]*50,50,(0,1))['indexes'])==50
    with pytest.raises(ValueError) as exc:resample([1]*51,50,(0,1))
    assert str(exc.value)=='weights must be an exact list with 1..50 entries'
    with pytest.raises(ValueError) as exc:resample([1],51,(0,1))
    assert str(exc.value)=='count must be an integer in 1..50'


@pytest.mark.parametrize('bad',[True,1.5,I(1),-1001,1001])
def test_kalman_measurement_position_validation(bad):
    for call in (lambda:kalman(0,1,bad,1),lambda:kalman(bad,1,0,1)):
        with pytest.raises(ValueError) as exc:call()
        assert str(exc.value)=='mean and measurement must be integers in -1000..1000'


@pytest.mark.parametrize('bad',[True,1.5,I(1),-101,101])
def test_ekf_measurement_position_validation(bad):
    for call in (lambda:ekf(0,1,bad,1),lambda:ekf(bad,1,0,1)):
        with pytest.raises(ValueError) as exc:call()
        assert str(exc.value)=='mean and measurement must be integers in -100..100'


def test_scalar_numeric_all_boundaries():
    for m in (-1000,1000):
        assert kalman(m,1000,m,1000)['mean']==(m,1)
    for m in (-100,100):
        assert ekf(m,100,m,100)['claim']=='PARTIAL'
        assert transform(m,100)['claim']=='PARTIAL'
    for call,message in [(lambda:kalman(0,1001,0,1),'variance must be an integer in 0..1000'),
                         (lambda:kalman(0,1,0,1001),'noise must be an integer in 1..1000'),
                         (lambda:ekf(0,101,0,1),'variance must be an integer in 0..100'),
                         (lambda:ekf(0,1,0,101),'noise must be an integer in 1..100'),
                         (lambda:transform(0,101),'spread must be an integer in 1..100')]:
        with pytest.raises(ValueError) as exc:call()
        assert str(exc.value)==message
