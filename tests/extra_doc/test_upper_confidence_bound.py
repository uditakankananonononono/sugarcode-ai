from fractions import Fraction as F
import inspect
import pytest
from sugarcode.extra_doc.upper_confidence_bound import upper_confidence_bound


def test_counts_means_and_exact_exploration():
    r=upper_confidence_bound(3,[(0,1),(0,0),(1,1),(2,0)],log_value=F(1),coefficient=2)
    assert r['counts']==[2,1,1]
    assert r['means']==[F(1,2),1,0]
    assert r['bonus_squared']==[1,2,2]
    assert r['chosen_arm']==1


def test_untried_priority_and_ties():
    assert upper_confidence_bound(3,[(1,1)],log_value=F(0))['chosen_arm']==0
    r=upper_confidence_bound(2,[(0,1),(1,1)],log_value=F(1))
    assert r['chosen_arm']==0
    assert upper_confidence_bound(2,[(0,1),(1,0)],log_value=F(0))['chosen_arm']==0


def test_squared_exploration_oracle():
    # Bonuses are rational perfect squares here, so compare exact literal scores.
    for a in range(5):
        for b in range(5):
            rows=[(0,F(a,4)),(1,F(b,4))]
            r=upper_confidence_bound(2,rows,log_value=F(2),coefficient=2)
            assert r['means']==[F(a,4),F(b,4)]
            assert r['chosen_arm']==(0 if a>=b else 1)


def test_unequal_count_optimism():
    rows=[(0,1)]*4+[(1,F(1,2))]
    assert upper_confidence_bound(2,rows,log_value=F(0))['chosen_arm']==0
    assert upper_confidence_bound(2,rows,log_value=F(2),coefficient=2)['chosen_arm']==1


@pytest.mark.parametrize('arms',[True,None,1.,'1',0,5])
def test_arm_refusal(arms):
    with pytest.raises((TypeError,ValueError)):upper_confidence_bound(arms,[],log_value=0)


@pytest.mark.parametrize('feedback',[None,(),[(0,1)]*101,[None],[(0,)],[('0',1)],[(True,1)],[(2,1)],[(0,True)],[(0,1.)],[(0,-1)],[(0,2)],[(0,F(1,10**101))]])
def test_feedback_refusal(feedback):
    with pytest.raises((TypeError,ValueError)):upper_confidence_bound(2,feedback,log_value=0)


@pytest.mark.parametrize('value',[True,None,.1,'1',-1,101,F(1,10**101)])
def test_log_refusal(value):
    with pytest.raises((TypeError,ValueError)):upper_confidence_bound(1,[],log_value=value)


@pytest.mark.parametrize('value',[True,None,1.,'1',-1,11])
def test_coefficient_refusal(value):
    with pytest.raises((TypeError,ValueError)):upper_confidence_bound(1,[],log_value=0,coefficient=value)


def test_caps_preflight_and_defaults():
    class Rows(list):
        def __iter__(self):raise AssertionError('overbudget scanned')
    with pytest.raises(ValueError):upper_confidence_bound(1,Rows([None]*101),log_value=0)
    assert inspect.signature(upper_confidence_bound).parameters['coefficient'].default==2
    r=upper_confidence_bound(4,[(0,1)]*100,log_value=100,coefficient=10)
    assert r['counts']==[100,0,0,0] and r['chosen_arm']==1
    assert upper_confidence_bound(1,[(0,F(1,10**100))],log_value=F(1,10**100),coefficient=0)['chosen_arm']==0


def test_radical_order_square_oracle():
    from sugarcode.extra_doc.upper_confidence_bound import _compare
    import itertools
    for m,n,a,b in itertools.product(range(-1,3),range(-1,3),range(4),range(4)):
        assert _compare(F(m),F(a*a),F(n),F(b*b))==((m+a>n+b)-(m+a<n+b))
    assert _compare(F(2),F(2),F(0),F(12))==-1
    assert _compare(F(3),F(2),F(0),F(12))==1
