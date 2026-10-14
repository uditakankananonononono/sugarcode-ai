import itertools
import random
import time
import pytest
from sugarcode.extra_doc.knapsack_best import best_selection as bs

T, V = TypeError, ValueError


def oracle(items, cap):
    best = None
    for k in range(len(items) + 1):
        for comb in itertools.combinations(range(len(items)), k):    # lists in lexicographic order within a size
            w = sum(items[i][0] for i in comb)
            if w > cap:
                continue
            v = sum(items[i][1] for i in comb)
            key = (v, -w)
            if best is None or key > best[0] or (key == best[0] and list(comb) < best[1]):
                best = (key, list(comb))
    return {'value': best[0][0], 'weight': -best[0][1], 'chosen': best[1]}


def test_hand_cases_exact():
    assert bs([(5, 10), (4, 40), (6, 30), (3, 50)], 10) == {'value': 90, 'weight': 7, 'chosen': [1, 3]}
    assert bs([], 0) == {'value': 0, 'weight': 0, 'chosen': []}
    assert bs([], 10000) == {'value': 0, 'weight': 0, 'chosen': []}
    assert bs([(1, 0)], 5) == {'value': 0, 'weight': 0, 'chosen': []}           # a worthless item is left out
    assert bs([(2, 3), (2, 3)], 2) == {'value': 3, 'weight': 2, 'chosen': [0]}  # tie: earlier position
    assert bs([(2, 3), (2, 3)], 4) == {'value': 6, 'weight': 4, 'chosen': [0, 1]}
    assert bs([(5, 5)], 4) == {'value': 0, 'weight': 0, 'chosen': []}
    assert bs([(5, 5)], 5) == {'value': 5, 'weight': 5, 'chosen': [0]}
    # same value, lighter weight wins even if it sits later in the list
    assert bs([(4, 7), (3, 7)], 4) == {'value': 7, 'weight': 3, 'chosen': [1]}
    # greedy by value-per-weight would take item 0 (ratio 6) and stop at 6; the best is 1+2 = 10


def test_random_vs_oracle():
    rnd = random.Random(574)
    ties = 0
    for _ in range(600):
        items = [(rnd.randint(1, 6), rnd.randint(0, 6)) for _ in range(rnd.randint(0, 9))]
        cap = rnd.randint(0, 20)
        got = bs(items, cap)
        want = oracle(items, cap)
        assert got == want
        ties += len(want['chosen']) >= 2
    assert ties > 100


def test_largest_case():
    t0 = time.time()
    items = [(1000 - i, 999999 - i) for i in range(20)]
    r = bs(items, 10000)
    assert time.time() - t0 < 5
    assert r['weight'] <= 10000 and r['value'] == sum(items[i][1] for i in r['chosen'])
    assert r['weight'] == sum(items[i][0] for i in r['chosen'])
    assert bs([(1000, 1000000)] * 10, 10000) == {'value': 10000000, 'weight': 10000, 'chosen': list(range(10))}
    assert bs([(1000, 1000000)] * 20, 10000)['chosen'] == list(range(10))


def err(f, exc, msg, *a):
    with pytest.raises(exc) as e:
        f(*a)
    assert str(e.value) == msg


def test_pins():
    err(bs, T, 'items must be a list or tuple', 'ab', 1)
    err(bs, T, 'items must be a list or tuple', {(1, 1)}, 1)
    err(bs, V, 'item count must be between 0 and 20', [(1, 1)] * 21, 1)
    for bad in ('ab', 5, None, (1,), (1, 2, 3), {1: 1, 2: 2}):
        err(bs, T, 'each item must be a (weight, value) pair', [(1, 1), bad], 1)
    for bad in (True, 1.0, '1', None):
        err(bs, T, 'weight must be a nonbool int', [(bad, 1)], 1)
        err(bs, T, 'value must be a nonbool int', [(1, bad)], 1)
        err(bs, T, 'capacity must be a nonbool int', [(1, 1)], bad)
    err(bs, V, 'weight must be between 1 and 1000', [(0, 1)], 1)
    err(bs, V, 'weight must be between 1 and 1000', [(1001, 1)], 1)
    err(bs, V, 'value must be between 0 and 1000000', [(1, -1)], 1)
    err(bs, V, 'value must be between 0 and 1000000', [(1, 1000001)], 1)
    err(bs, V, 'capacity must be between 0 and 10000', [(1, 1)], -1)
    err(bs, V, 'capacity must be between 0 and 10000', [(1, 1)], 10001)


def test_edges_accepted():
    bs([(1, 1)] * 20, 0)
    bs([(1000, 0)], 10000)
    bs([(1, 1000000)], 0)
    assert bs([(1000, 1000000)], 1000)['value'] == 1000000


def test_order_and_every_position():
    err(bs, T, 'items must be a list or tuple', 'x', 'y')
    err(bs, V, 'item count must be between 0 and 20', [(1, 1)] * 21, 'y')
    err(bs, T, 'weight must be a nonbool int', [(1.5, 0)], 'y')
    err(bs, T, 'value must be a nonbool int', [(0, 1.5)], 'y')               # type of both before the ranges
    err(bs, V, 'weight must be between 1 and 1000', [(0, -1)], 'y')           # weight range before value range
    err(bs, T, 'each item must be a (weight, value) pair', [5, (0, 0)], 'y')
    err(bs, V, 'weight must be between 1 and 1000', [(0, 1), 5], 1)
    err(bs, V, 'capacity must be between 0 and 10000', [(1, 1)], 10 ** 6)
    for pos in range(3):
        its = [(1, 1), (2, 2), (3, 3)]
        its[pos] = (1, 2.5)
        err(bs, T, 'value must be a nonbool int', its, 5)
        its[pos] = (0, 1)
        err(bs, V, 'weight must be between 1 and 1000', its, 5)
        its[pos] = 7
        err(bs, T, 'each item must be a (weight, value) pair', its, 5)


def test_greedy_by_ratio_is_not_optimal():
    # ratio order takes the 6-weight item (30) and then nothing fits; the two 5-weight items give 32
    assert bs([(6, 30), (5, 16), (5, 16)], 10) == {'value': 32, 'weight': 10, 'chosen': [1, 2]}
