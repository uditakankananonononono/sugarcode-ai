"""Row 357 tests-only hardening: oracle, caps at N and N+1, exact messages, exact-type pins, check order."""
import itertools

import pytest

from sugarcode.extra_doc.adversarial_design import productive_friction as pf


class L(list):
    pass


class T(tuple):
    pass


class I(int):
    pass


def refuses(error, msg, *a):
    with pytest.raises(error) as e:
        pf(*a)
    assert type(e.value) is error and str(e.value) == msg


TY = 'friction and benefits must be lists or tuples'
FC = 'feature count must be between 1 and 12'
BC = 'benefit count must match features'
BG = 'budget must be a nonbool integer zero through 1000000'
VL = 'friction and benefits must be nonbool integers zero through 1000000'


def oracle(fr, be, bud):
    best, feas = None, 0
    for r in range(len(fr) + 1):
        for ch in itertools.combinations(range(len(fr)), r):
            c = sum(fr[i] for i in ch)
            if c > bud:
                continue
            feas += 1
            key = (-sum(be[i] for i in ch), c, ch)
            if best is None or key < best:
                best = key
    return best, feas


CASES = [
    ([3, 4, 2], [5, 6, 3], 6),
    ([3, 4, 2], [5, 6, 3], 5),
    ([3, 4, 2], [5, 6, 3], 0),
    ([1, 1, 1], [2, 2, 2], 2),
    ([2, 1], [3, 3], 3),
    ([0, 0], [0, 0], 5),
    ([5], [9], 4),
    ([5], [9], 5),
    ([1, 2, 3, 4], [1, 2, 3, 4], 10),
    ([4, 3], [4, 3], 3),
]


@pytest.mark.parametrize('fr,be,bud', CASES)
def test_oracle(fr, be, bud):
    (neg, cost, ch), feas = oracle(fr, be, bud)
    assert pf(fr, be, bud) == {'feature_indices': list(ch), 'friction': cost, 'benefit': -neg, 'feasible_count': feas,
                               'behavior_change_validated': False}


def test_literals_and_ties():
    assert pf([3, 4, 2], [5, 6, 3], 6) == {'feature_indices': [1, 2], 'friction': 6, 'benefit': 9, 'feasible_count': 6,
                                          'behavior_change_validated': False}
    assert pf([2, 1], [3, 3], 3)['feature_indices'] == [0, 1]
    assert pf([2, 1], [3, 0], 3)['feature_indices'] == [0]                     # same benefit: less friction wins
    assert pf([1, 1], [3, 3], 1)['feature_indices'] == [0]                     # full tie: lowest index tuple
    assert pf([1, 1], [0, 0], 5)['feature_indices'] == []                      # zero benefit: empty set (less friction)
    assert pf([5], [9], 5)['feature_indices'] == [0] and pf([5], [9], 4)['feature_indices'] == []
    assert pf([1] * 12, [1] * 12, 1000000)['feasible_count'] == 4096
    assert pf([1] * 12, [1] * 12, 0)['feasible_count'] == 1
    assert pf([0] * 12, [1] * 12, 0)['feasible_count'] == 4096


def test_caps_n_and_n_plus_1():
    refuses(ValueError, FC, [1] * 13, [1] * 13, 1)
    refuses(ValueError, FC, [], [], 1)
    refuses(ValueError, BC, [1], [1, 1], 1)
    refuses(ValueError, BC, [1, 1], [1], 1)
    for b in (-1, 1000001):
        refuses(ValueError, BG, [1], [1], b)
        refuses(ValueError, VL, [b], [1], 1)
        refuses(ValueError, VL, [1, b], [1, 1], 1)
        refuses(ValueError, VL, [1], [b], 1)
        refuses(ValueError, VL, [1, 1], [1, b], 1)
    assert pf([1000000], [1000000], 1000000)['benefit'] == 1000000
    assert pf([0], [0], 0)['feasible_count'] == 2


def test_exact_types():
    refuses(TypeError, TY, L([1]), [1], 1)
    refuses(TypeError, TY, T((1,)), [1], 1)
    refuses(TypeError, TY, [1], L([1]), 1)
    refuses(TypeError, TY, [1], T((1,)), 1)
    for b in (None, 'a', {1}, {1: 1}, 5):
        refuses(TypeError, TY, b, [1], 1)
        refuses(TypeError, TY, [1], b, 1)
    for b in (True, False, 1.0, I(1), '1', None):
        refuses(ValueError, BG, [1], [1], b)
        refuses(ValueError, VL, [b], [1], 1)
        refuses(ValueError, VL, [1, b], [1, 1], 1)
        refuses(ValueError, VL, [1], [b], 1)
        refuses(ValueError, VL, [1, 1], [1, b], 1)
    assert pf((1,), (1,), 1) == pf([1], [1], 1)
    f = [1]
    r = pf(f, [1], 1)
    r['feature_indices'].append(5)
    assert f == [1]


def test_check_order():
    refuses(TypeError, TY, 1, 2, 3)
    refuses(ValueError, FC, [], [], True)
    refuses(ValueError, BC, [True], [], True)
    refuses(ValueError, BG, [True], [True], True)
    refuses(ValueError, VL, [True], [True], 1)
