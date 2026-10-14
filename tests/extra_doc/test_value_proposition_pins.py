"""Row 363 tests-only hardening: oracle, caps at N and N+1, exact messages, exact-type pins, check order."""
import itertools

import pytest

from sugarcode.extra_doc.value_proposition import design_offer as do


class L(list):
    pass


class T(tuple):
    pass


class I(int):
    pass


def refuses(error, msg, *a):
    with pytest.raises(error) as e:
        do(*a)
    assert type(e.value) is error and str(e.value) == msg


TY = 'inputs must be lists or tuples'
CNT = 'feature count must be 1..12 and need count 1..16'
ROW = 'coverage rows must match features and contain at most 16 indices'
VAL = 'costs importance and budget must be nonbool integers zero through 1000000'
IDX = 'need indices must be nonbool valid indices'
UNI = 'need indices must be unique'


def oracle(costs, cov, imp, bud):
    best = None
    for r in range(len(costs) + 1):
        for ch in itertools.combinations(range(len(costs)), r):
            c = sum(costs[i] for i in ch)
            if c > bud:
                continue
            covered = sorted({j for i in ch for j in cov[i]})
            key = (-sum(imp[j] for j in covered), c, len(ch), ch)
            if best is None or key < best[0]:
                best = (key, covered)
    (neg, c, _, ch), covered = best
    return {'feature_indices': list(ch), 'covered_needs': covered, 'importance': -neg, 'cost': c,
            'customer_response_validated': False}


CASES = [
    ([3, 2, 4], [[0, 1], [1], [2]], [5, 4, 3], 5),
    ([3, 2, 4], [[0, 1], [1], [2]], [5, 4, 3], 9),
    ([3, 2, 4], [[0, 1], [1], [2]], [5, 4, 3], 0),
    ([1, 1], [[0], [0]], [7], 2),
    ([2, 1], [[0], [0]], [7], 2),
    ([1, 1, 1], [[0], [1], [0, 1]], [1, 1], 2),
    ([0, 0], [[], []], [1, 2], 3),
    ([5], [[0, 1, 2]], [0, 0, 0], 5),
    ([2, 2, 2, 2], [[0], [1], [2], [0, 1, 2]], [3, 3, 3], 4),
]


@pytest.mark.parametrize('c,cov,imp,b', CASES)
def test_oracle(c, cov, imp, b):
    assert do(c, cov, imp, b) == oracle(c, cov, imp, b)


def test_literals_and_ties():
    assert do([3, 2, 4], [[0, 1], [1], [2]], [5, 4, 3], 5) == {'feature_indices': [0], 'covered_needs': [0, 1], 'importance': 9,
                                                              'cost': 3, 'customer_response_validated': False}
    assert do([1, 1], [[0], [0]], [7], 2)['feature_indices'] == [0]                 # need counted once; lower cost then fewer
    assert do([2, 1], [[0], [0]], [7], 2)['feature_indices'] == [1]
    assert do([1, 1], [[0], [0]], [7], 1)['feature_indices'] == [0]                 # full tie: lexicographic
    assert do([0, 0], [[], []], [1], 0)['feature_indices'] == []                    # nothing worth buying
    assert do([5], [[0]], [3], 5)['feature_indices'] == [0] and do([5], [[0]], [3], 4)['feature_indices'] == []
    assert do([0] * 12, [[0]] * 12, [1], 0)['feature_indices'] == [0]


def test_caps_and_bounds_n_and_n_plus_1():
    assert do([1] * 12, [[]] * 12, [1] * 16, 12)['importance'] == 0
    refuses(ValueError, CNT, [1] * 13, [[]] * 13, [1], 1)
    refuses(ValueError, CNT, [], [], [1], 1)
    assert do([1], [[]], [1] * 16, 1)['cost'] == 0
    refuses(ValueError, CNT, [1], [[]], [1] * 17, 1)
    refuses(ValueError, CNT, [1], [[]], [], 1)
    refuses(ValueError, ROW, [1], [[], []], [1], 1)
    refuses(ValueError, ROW, [1, 1], [[]], [1], 1)
    assert do([1], [list(range(16))], [1] * 16, 1)['covered_needs'] == list(range(16))
    refuses(ValueError, ROW, [1], [list(range(17))], [1] * 16, 1)
    refuses(ValueError, ROW, [1, 1], [[], [0] * 17], [1] * 16, 1)
    for b in (-1, 1000001):
        refuses(ValueError, VAL, [b], [[]], [1], 1)
        refuses(ValueError, VAL, [1, b], [[], []], [1], 1)
        refuses(ValueError, VAL, [1], [[]], [b], 1)
        refuses(ValueError, VAL, [1], [[]], [1, b], 1)
        refuses(ValueError, VAL, [1], [[]], [1], b)
    assert do([1000000], [[0]], [1000000], 1000000)['importance'] == 1000000
    for b in (-1, 1):
        refuses(ValueError, IDX, [1], [[b]], [1], 1)
        refuses(ValueError, IDX, [1, 1], [[0], [0, b]], [1], 1)
    refuses(ValueError, IDX, [1], [[16]], [1] * 16, 1)
    refuses(ValueError, UNI, [1], [[0, 0]], [1], 1)
    refuses(ValueError, UNI, [1, 1], [[0], [0, 0]], [1], 1)


def test_exact_types():
    refuses(TypeError, TY, L([1]), [[]], [1], 1)
    refuses(TypeError, TY, [1], L([[]]), [1], 1)
    refuses(TypeError, TY, [1], [[]], L([1]), 1)
    refuses(TypeError, TY, T((1,)), [[]], [1], 1)
    for b in (None, 'a', {1}, {1: 1}, 5):
        refuses(TypeError, TY, b, [[]], [1], 1)
        refuses(TypeError, TY, [1], b, [1], 1)
        refuses(TypeError, TY, [1], [[]], b, 1)
    refuses(ValueError, ROW, [1], [L([])], [1], 1)
    refuses(ValueError, ROW, [1, 1], [[], T(())], [1], 1)
    refuses(ValueError, ROW, [1, 1], [[], 'a'], [1], 1)
    for b in (True, False, 1.0, I(1), '1', None):
        refuses(ValueError, VAL, [b], [[]], [1], 1)
        refuses(ValueError, VAL, [1, b], [[], []], [1], 1)
        refuses(ValueError, VAL, [1], [[]], [b], 1)
        refuses(ValueError, VAL, [1], [[]], [1, b], 1)
        refuses(ValueError, VAL, [1], [[]], [1], b)
    for b in (True, I(0), 0.0, '0', None):
        refuses(ValueError, IDX, [1], [[b]], [1], 1)
        refuses(ValueError, IDX, [1, 1], [[0], [0, b]], [1], 1)
    assert do((1,), ((0,),), (1,), 1) == do([1], [[0]], [1], 1)
    c = [[0]]
    r = do([1], c, [1], 1)
    r['covered_needs'].append(9)
    assert c == [[0]]


def test_check_order():
    refuses(TypeError, TY, 1, 2, 3, 4)
    refuses(ValueError, CNT, [], [], [], True)
    refuses(ValueError, ROW, [1], [], [1], True)
    refuses(ValueError, VAL, [True], [[5]], [1], 1)
    refuses(ValueError, IDX, [1], [[5]], [1], 1)
    refuses(ValueError, UNI, [1], [[0, 0]], [1], 1)
