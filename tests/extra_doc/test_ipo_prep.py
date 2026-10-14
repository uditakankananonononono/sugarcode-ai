import pytest
from fractions import Fraction as F
from sugarcode.extra_doc.ipo_prep import checklist_progress as cp, offering_math as om, NOT_CLAIMED

ITEMS = [('a', 4, 2), ('b', 3, 1), ('c', 2, 0), ('d', 1, 2)]


def test_progress_oracle():
    r = cp(ITEMS, 3)
    assert r['total_weight'] == 10 and r['done_share'] == F(1, 2) and r['in_progress_share'] == F(3, 10)
    assert r['blockers'] == ('b',)
    assert r['ipo_validated'] is False and r['not_claimed'] == NOT_CLAIMED and len(NOT_CLAIMED) == 8


def test_progress_edges():
    assert cp(ITEMS, 1)['blockers'] == ('b', 'c')
    assert cp(ITEMS, 4)['blockers'] == ()
    assert cp([('x', 10, 2)], 10)['done_share'] == 1
    assert cp([('x' * 40, 10, 2)], 10)['done_share'] == 1
    with pytest.raises(ValueError, match='unique'):
        cp([('a', 1, 0), ('a', 2, 0)], 3)


def test_offering_oracle():
    r = om(1000000, 250000, 40)
    assert r['gross_proceeds'] == 10000000 and r['pre_money'] == 40000000 and r['post_money'] == 50000000
    assert r['existing_share'] == F(4, 5) and r['new_investor_share'] == F(1, 5)
    assert r['ipo_validated'] is False


def test_offering_edges():
    r = om(10 ** 10, 0, 10 ** 9)
    assert r['gross_proceeds'] == 0 and r['new_investor_share'] == 0 and r['existing_share'] == 1
    r = om(1, 10 ** 10, 1)
    assert r['gross_proceeds'] == 10 ** 10 and r['post_money'] == 10 ** 10 + 1


@pytest.mark.parametrize('args,exc,msg', [
    ((ITEMS, True), TypeError, 'cutoff'), ((ITEMS, 1.0), TypeError, 'cutoff'),
    ((ITEMS, 0), ValueError, 'cutoff'), ((ITEMS, 11), ValueError, 'cutoff'),
    (('x', 3), TypeError, 'list or tuple'), (([], 3), ValueError, 'between 1 and 20'),
    (([('a', 1, 0)] * 21, 3), ValueError, 'between 1 and 20'),
    (([('a', 1)], 3), ValueError, 'each item'), ((['abc'], 3), ValueError, 'each item'),
    (([{'a': 1}], 3), ValueError, 'each item'),
    (([(1, 1, 0)], 3), TypeError, 'names must be str'), (([('', 1, 0)], 3), ValueError, '1 to 40'),
    (([('x' * 41, 1, 0)], 3), ValueError, '1 to 40'),
    (([('a', True, 0)], 3), TypeError, 'nonbool'), (([('a', 1, 1.0)], 3), TypeError, 'nonbool'),
    (([('a', 1, True)], 3), TypeError, 'nonbool'),
    (([('a', 0, 0)], 3), ValueError, 'weight'), (([('a', 11, 0)], 3), ValueError, 'weight'),
    (([('a', 1, -1)], 3), ValueError, 'status'), (([('a', 1, 3)], 3), ValueError, 'status'),
    (([('a', 1, 0), ('a', 1, 0)], 3), ValueError, 'unique'),
])
def test_progress_refusals(args, exc, msg):
    with pytest.raises(exc, match=msg):
        cp(*args)


@pytest.mark.parametrize('args,exc,msg', [
    ((True, 1, 1), TypeError, 'pre_shares'), ((1.0, 1, 1), TypeError, 'pre_shares'),
    ((1, True, 1), TypeError, 'new_shares'), ((1, 1, 1.0), TypeError, 'price'),
    ((0, 1, 1), ValueError, 'pre_shares'), ((10 ** 10 + 1, 1, 1), ValueError, 'pre_shares'),
    ((1, -1, 1), ValueError, 'new_shares'), ((1, 10 ** 10 + 1, 1), ValueError, 'new_shares'),
    ((1, 1, 0), ValueError, 'price'), ((1, 1, 10 ** 9 + 1), ValueError, 'price'),
])
def test_offering_refusals(args, exc, msg):
    with pytest.raises(exc, match=msg):
        om(*args)


def test_bounds_ok():
    r = cp([('i%d' % i, 10, 2) for i in range(20)], 10)
    assert r['total_weight'] == 200 and r['done_share'] == 1


def test_cap_before_scan():
    with pytest.raises(ValueError, match='between 1 and 20'):
        cp(['x'] * 10 ** 6, 3)
