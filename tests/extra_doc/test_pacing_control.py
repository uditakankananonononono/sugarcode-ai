from fractions import Fraction as F
from itertools import product
import pytest
from sugarcode.extra_doc.pacing_control import pacing_control


def test_generated_schedule_matches_exhaustive_oracle():
    beats=[('setup',1,4),('action',2,5),('release',1,3)]
    targets=[3,2,3]
    r=pacing_control(beats,targets,8)
    feasible=[x for x in product(range(1,5),range(2,6),range(1,4)) if sum(x)==8]
    expected=min(feasible,key=lambda x:(sum((a-b)**2 for a,b in zip(x,targets)),x))
    assert r['durations']==list(expected)
    assert r['schedule']==list(zip(['setup','action','release'],expected))
    assert r['certificate']=={'total':8,'objective':F(0),'bounds_satisfied':True,'optimal':True}


def test_tie_break_and_active_constraints():
    r=pacing_control([('a',1,3),('b',1,3)],[2,2],3)
    assert r['durations']==[1,2] and r['certificate']['objective']==1
    assert pacing_control([('a',2,2),('b',1,4)],[0,8],5)['durations']==[2,3]


def test_small_grid_oracle():
    for total in range(2,7):
        for a in range(4):
            for b in range(4):
                xs=[x for x in product(range(1,4),repeat=2) if sum(x)==total]
                expected=min(xs,key=lambda x:(sum((u-v)**2 for u,v in zip(x,[a,b])),x))
                assert pacing_control([('a',1,3),('b',1,3)],[a,b],total)['durations']==list(expected)


@pytest.mark.parametrize('beats',[None,(),[],[None],[('a',0,1)],[('a',1,9)],[('a',3,2)],[('a',True,2)],[('a',1.,2)],[('',1,2)],[('x'*21,1,2)],[('a',1,2)]*7])
def test_beat_refusal(beats):
    with pytest.raises((TypeError,ValueError)):pacing_control(beats,[1],1)


@pytest.mark.parametrize('targets',[None,(),[],[True],[1.],[-1],[9],[1,2]])
def test_target_refusal(targets):
    with pytest.raises((TypeError,ValueError)):pacing_control([('a',1,2)],targets,1)


@pytest.mark.parametrize('total',[True,None,1.,0,49,3])
def test_total_refusal(total):
    with pytest.raises((TypeError,ValueError)):pacing_control([('a',1,2)],[1],total)


def test_endpoints_and_preflight():
    class Rows(list):
        def __iter__(self):raise AssertionError('oversized scanned')
    with pytest.raises(ValueError):pacing_control(Rows([None]*7),[1],1)
    r=pacing_control([('x'*20,8,8)]*6,[8]*6,48)
    assert r['durations']==[8]*6
    assert pacing_control([('a',1,1)],[0],1)['certificate']['objective']==1


def test_isolated_preflight_guards_with_otherwise_valid_inputs():
    with pytest.raises(ValueError,match='one target per beat required'):
        pacing_control([('a',1,2)],(1,),1)
    with pytest.raises(ValueError,match='label/min/max beat required'):
        pacing_control([['a',1,2]],[1],1)
    for lo,hi,total in [(0,2,1),(1,9,1),(9,9,9),(1,0,1)]:
        with pytest.raises(ValueError,match='integer cap or range exceeded'):
            pacing_control([('a',lo,hi)],[1],total)
    with pytest.raises(ValueError,match='beat cap 1..6 required'):
        pacing_control([('a',1,1)]*7,[1]*7,7)
    assert pacing_control([('a',1,8)],[1],1)['durations']==[1]
    assert pacing_control([('a',1,8)],[8],8)['durations']==[8]


def test_total_and_empty_preflight_exact_precedence():
    for total in (0,49):
        with pytest.raises(ValueError,match='^integer cap or range exceeded$'):
            pacing_control([('a',1,8)],[1],total)
    assert pacing_control([('a',8,8)]*6,[8]*6,48)['durations']==[8]*6
    with pytest.raises(ValueError,match='^beat cap 1..6 required$'):
        pacing_control([],[],1)
    with pytest.raises(ValueError,match='^integer cap or range exceeded$'):
        pacing_control([('a',1,9)],[1],9)
    assert pacing_control([('a',1,8)],[1],8)['durations']==[8]


def test_lo_upper_cap_precedes_min_max_consistency():
    with pytest.raises(ValueError,match='^integer cap or range exceeded$'):
        pacing_control([('a',9,8)],[1],8)
    assert pacing_control([('a',8,8)],[1],8)['durations']==[8]
