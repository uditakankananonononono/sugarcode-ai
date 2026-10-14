from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.kotter_steps import kotter_progress as solve, STEPS, NOT_CLAIMED


def test_hand_derived_literal():
    r = solve([2, 2, 1, 0, 2, 0, 0, 0])
    assert (r['done'], r['in_progress'], r['done_share']) == (3, 1, F(3, 8))
    assert r['first_not_done'] == 3 and r['first_not_done_name'] == 'Form a strategic vision'
    assert r['out_of_order'] == (5,)              # step 5 is done while step 4 was never started
    assert type(r['done_share']) is F and r['change_validated'] is False and r['not_claimed'] == NOT_CLAIMED


def test_step_names_and_order_literal():
    assert STEPS == ('Create a sense of urgency', 'Build a guiding coalition', 'Form a strategic vision',
                     'Enlist a volunteer army', 'Enable action by removing barriers', 'Generate short-term wins',
                     'Sustain acceleration', 'Institute change')
    for i in range(8):
        s = [2] * i + [0] * (8 - i)
        r = solve(s)
        assert r['first_not_done'] == i + 1 and r['first_not_done_name'] == STEPS[i]


def test_all_done_and_none_started():
    r = solve([2] * 8)
    assert r['first_not_done'] is None and r['first_not_done_name'] is None and r['done'] == 8
    assert r['done_share'] == 1 and r['out_of_order'] == ()
    r = solve([0] * 8)
    assert r['first_not_done'] == 1 and r['done'] == 0 and r['done_share'] == 0 and r['out_of_order'] == ()
    assert solve([1] * 8)['in_progress'] == 8


def test_out_of_order_rules():
    assert solve([0, 2, 2, 2, 2, 2, 2, 2])['out_of_order'] == (2, 3, 4, 5, 6, 7, 8)
    assert solve([0, 1, 0, 0, 0, 0, 0, 0])['out_of_order'] == (2,)
    assert solve([1, 1, 1, 1, 1, 1, 1, 1])['out_of_order'] == ()              # in progress everywhere is in order
    assert solve([2, 2, 2, 2, 2, 2, 2, 0])['out_of_order'] == ()
    assert solve([2, 0, 0, 0, 0, 0, 0, 1])['out_of_order'] == (8,)
    assert solve([2, 1, 0, 0, 0, 0, 0, 0])['out_of_order'] == ()


def test_refusals():
    for n in (7, 9, 0):
        with pytest.raises(ValueError, match='8 entries'):
            solve([0] * n)
    for bad in (3, -1):
        with pytest.raises(ValueError, match='0, 1 or 2'):
            solve([bad] + [0] * 7)
    for bad in (True, 1.0, '1'):
        with pytest.raises(TypeError, match='nonbool'):
            solve([bad] + [0] * 7)
    with pytest.raises(TypeError, match='list or tuple'):
        solve('x')
    with pytest.raises(ValueError, match='8 entries'):
        solve([None] * 10 ** 6)


def test_no_mutation():
    s = [1] * 8
    solve(s)
    assert s == [1] * 8
