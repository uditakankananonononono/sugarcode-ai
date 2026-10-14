import itertools
import random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.tolerance_stack import stack_up as st


def oracle(items, lo, hi):
    # brute force: every corner of every band (extremes of a linear sum are at corners)
    corners = []
    for n, p, m, s in items:
        corners.append([s * (F(n) - F(m)), s * (F(n) + F(p))])
    sums = [sum(c) for c in itertools.product(*corners)]
    low, high = min(sums), max(sums)
    nominal = sum(s * F(n) for n, p, m, s in items)
    mean = sum(s * (F(n) + (F(p) - F(m)) / 2) for n, p, m, s in items)
    spread2 = sum(((F(p) + F(m)) / 2) ** 2 for n, p, m, s in items)
    rss = (mean >= lo and mean <= hi and (mean - lo) ** 2 >= spread2 and (hi - mean) ** 2 >= spread2)
    tot = high - low
    return dict(nominal_gap=nominal, worst_low=low, worst_high=high, worst_case_ok=lo <= low and high <= hi,
                mean_gap=mean, spread_squared=spread2, rss_ok=rss,
                shares=[(F(p) + F(m)) / tot if tot else F(0) for n, p, m, s in items])


def test_random_vs_bruteforce():
    rnd = random.Random(6)
    for _ in range(400):
        items = [(F(rnd.randint(0, 50), rnd.randint(1, 4)), F(rnd.randint(0, 6), rnd.randint(1, 3)),
                  F(rnd.randint(0, 6), rnd.randint(1, 3)), rnd.choice([1, -1])) for _ in range(rnd.randint(1, 6))]
        lo = F(rnd.randint(-80, 20), rnd.randint(1, 3))
        hi = lo + F(rnd.randint(0, 100), rnd.randint(1, 3))
        assert st(items, lo, hi) == oracle(items, lo, hi)


def test_hand_case():
    # two parts: 10 +0.2/-0.1 adds, 4 +0.1/-0.1 subtracts. Gap between 5.7 and 6.3
    items = [(10, F(1, 5), F(1, 10), 1), (4, F(1, 10), F(1, 10), -1)]
    r = st(items, F(57, 10), F(63, 10))
    assert r['nominal_gap'] == 6 and r['worst_low'] == F(99, 10) - F(41, 10) and r['worst_high'] == F(102, 10) - F(39, 10)
    assert r['worst_low'] == F(58, 10) and r['worst_high'] == F(63, 10) and r['worst_case_ok'] is True
    assert r['mean_gap'] == F(1005, 100) - 4 and r['shares'] == [F(3, 10) / F(5, 10), F(2, 10) / F(5, 10)]
    assert st(items, F(581, 100), F(63, 10))['worst_case_ok'] is False
    assert st(items, F(57, 10), F(629, 100))['worst_case_ok'] is False
    assert st(items, F(58, 10), F(63, 10))['worst_case_ok'] is True


def test_rss_exact_edge():
    # one part 10 +-3 with limits 7..13: margin 3 each side, spread squared 9, so 9 >= 9 passes exactly
    r = st([(10, 3, 3, 1)], 7, 13)
    assert r['spread_squared'] == 9 and r['rss_ok'] is True and r['worst_case_ok'] is True
    assert st([(10, 3, 3, 1)], F(701, 100), 13)['rss_ok'] is False
    assert st([(10, 3, 3, 1)], 7, F(1299, 100))['rss_ok'] is False
    # RSS can pass where worst case fails
    r = st([(10, 2, 2, 1), (10, 2, 2, -1), (5, 2, 2, 1)], 1, 9)
    assert r['worst_case_ok'] is False and r['rss_ok'] is True
    # mean outside the limits fails even with zero spread
    assert st([(5, 0, 0, 1)], 6, 7)['rss_ok'] is False and st([(5, 0, 0, 1)], 3, 4)['rss_ok'] is False
    assert st([(5, 0, 0, 1)], 5, 5)['rss_ok'] is True
    assert st([(5, 0, 0, 1)], 5, 5)['shares'] == [0]


def test_caps_accept():
    st([(10000, 1000, 1000, 1)] * 12, -100000, 100000)
    st([(0, 0, 0, -1)], 0, 0)
    st(((F(1, 2 ** 32 - 1), 0, 0, 1),), F(-1, 2 ** 32 - 1), 0)


def err(exc, msg, *a):
    with pytest.raises(exc) as e:
        st(*a)
    assert str(e.value) == msg


T, V = TypeError, ValueError
OK = [(1, 0, 0, 1)]


def test_pins():
    err(T, 'items must be a list or tuple', 'a', 0, 1)
    err(V, 'item count must be between 1 and 12', [], 0, 1)
    err(V, 'item count must be between 1 and 12', OK * 13, 0, 1)
    err(T, 'each item must be (nominal, plus, minus, sign)', [3], 0, 1)
    err(T, 'each item must be (nominal, plus, minus, sign)', [(1, 0, 0)], 0, 1)
    err(T, 'each item must be (nominal, plus, minus, sign)', [(1, 0, 0, 1, 1)], 0, 1)
    for i, nm in enumerate(('nominal', 'plus', 'minus')):
        for bad in (True, 1.0, '1', None):
            it = [1, 0, 0, 1]
            it[i] = bad
            err(T, nm + ' must be a nonbool int or Fraction', [tuple(it)], 0, 1)
        it = [1, 0, 0, 1]
        it[i] = F(1, 2 ** 32)
        err(V, 'rational values must fit 32 bits', [tuple(it)], 0, 1)
        it[i] = 2 ** 32
        err(V, 'rational values must fit 32 bits', [tuple(it)], 0, 1)
    for bad in (True, 1.0, None, F(1)):
        err(T, 'sign must be a nonbool int', [(1, 0, 0, bad)], 0, 1)
    err(V, 'sign must be 1 or -1', [(1, 0, 0, 0)], 0, 1)
    err(V, 'sign must be 1 or -1', [(1, 0, 0, 2)], 0, 1)
    err(V, 'nominal must be between 0 and 10000', [(-1, 0, 0, 1)], 0, 1)
    err(V, 'nominal must be between 0 and 10000', [(10001, 0, 0, 1)], 0, 1)
    err(V, 'plus and minus must be between 0 and 1000', [(1, -1, 0, 1)], 0, 1)
    err(V, 'plus and minus must be between 0 and 1000', [(1, 1001, 0, 1)], 0, 1)
    err(V, 'plus and minus must be between 0 and 1000', [(1, 0, -1, 1)], 0, 1)
    err(V, 'plus and minus must be between 0 and 1000', [(1, 0, 1001, 1)], 0, 1)
    for bad in (True, 1.0, None):
        err(T, 'gap_min must be a nonbool int or Fraction', OK, bad, 1)
        err(T, 'gap_max must be a nonbool int or Fraction', OK, 0, bad)
    err(V, 'rational values must fit 32 bits', OK, F(1, 2 ** 32), 1)
    err(V, 'gap limits must be between -100000 and 100000', OK, -100001, 0)
    err(V, 'gap limits must be between -100000 and 100000', OK, 0, 100001)
    err(V, 'gap limits must be between -100000 and 100000', OK, 100001, 100001)
    err(V, 'gap limits must be between -100000 and 100000', OK, -100001, -100001)
    err(V, 'gap_min must not exceed gap_max', OK, 2, 1)


def test_validation_every_item():
    for pos in range(3):
        its = [(1, 0, 0, 1)] * 3
        its[pos] = (1, 0, 0, None)
        err(T, 'sign must be a nonbool int', its, 0, 1)
    err(V, 'gap_min must not exceed gap_max', [(1, 0, 0, 1), (2, 5, 5, -1)], 9, 1)


def test_limit_and_width_boundaries():
    st(OK, -100000, -100000)
    st(OK, 100000, 100000)
    st(OK, -100000, 100000)
    # out of range on one side only: the range message must win over the ordering message
    err(V, 'gap limits must be between -100000 and 100000', OK, -100000, -100001)
    err(V, 'gap limits must be between -100000 and 100000', OK, 100001, 100000)
    # 32-bit numerators and denominators, each alone at the edge
    st([(F(2 ** 31 + 1, 2 ** 31 + 3), 0, 0, 1)], 0, 1)
    st([(1, 0, 0, 1)], F(2 ** 31 + 1, 2 ** 31 + 3), 1)
    st([(1, 0, 0, 1)], 0, F(2 ** 32 - 2, 2 ** 32 - 1))
    err(V, 'rational values must fit 32 bits', [(F(2 ** 32 + 1, 2 ** 32 + 3), 0, 0, 1)], 0, 1)
