import importlib
import itertools
import random
from math import gcd

import pytest

from sugarcode.extra_doc.kalman_filter186 import kalman_filter

T, V = TypeError, ValueError


class L(list):
    pass


class I(int):
    pass


def red(n, d):
    g = gcd(n, d)
    return [n // g, d // g]


def oracle(zs, m0, p0, q, r):
    # track the variance as P = a/b and the estimate as m = c/d with explicit integers
    pa, pb = p0, 1
    ma, mb = m0, 1
    G, M, P = [], [], []
    for z in zs:
        pa, pb = pa + q * pb, pb               # p + q
        ga, gb = pa, pa + r * pb               # gain = p / (p + r) when p = pa/pb: (pa/pb) / ((pa + r pb)/pb)
        # estimate: m + g (z - m) = ma/mb + (ga/gb) * ((z mb - ma)/mb)
        na = ma * gb + ga * (z * mb - ma)
        nb = mb * gb
        ma, mb = na, nb
        # variance: (1 - g) p = ((gb - ga)/gb) * (pa/pb)
        pa, pb = (gb - ga) * pa, gb * pb
        G.append(red(ga, gb))
        M.append(red(ma, mb))
        P.append(red(pa, pb))
    return {'gains': G, 'estimates': M, 'variances': P, 'final': M[-1][:]}


def test_pins():
    assert kalman_filter([10, 10], 0, 1, 0, 1) == {
        'gains': [[1, 2], [1, 3]], 'estimates': [[5, 1], [20, 3]], 'variances': [[1, 2], [1, 3]], 'final': [20, 3]}
    assert kalman_filter([4], 0, 0, 0, 5) == {'gains': [[0, 1]], 'estimates': [[0, 1]], 'variances': [[0, 1]],
                                              'final': [0, 1]}
    assert kalman_filter([0, 10], 0, 0, 1, 1) == {
        'gains': [[1, 2], [3, 5]], 'estimates': [[0, 1], [6, 1]], 'variances': [[1, 2], [3, 5]], 'final': [6, 1]}
    r = kalman_filter([6, 6, 6], 0, 3, 1, 2)
    assert r['gains'] == [[2, 3], [7, 13], [27, 53]] and r['estimates'] == [[4, 1], [66, 13], [294, 53]]
    assert r['variances'] == [[4, 3], [14, 13], [54, 53]]
    r = kalman_filter([-100], 100, 100, 20, 1)
    assert r['gains'] == [[120, 121]] and r['estimates'] == [[-11900, 121]] and r['variances'] == [[120, 121]]


def test_types_keys():
    r = kalman_filter([1, 2, 3], 0, 1, 1, 1)
    assert list(r) == ['gains', 'estimates', 'variances', 'final']
    for k in ('gains', 'estimates', 'variances'):
        assert len(r[k]) == 3
        assert all(type(p) is list and len(p) == 2 and all(type(v) is int for v in p) and p[1] > 0 for p in r[k])
    assert r['final'] == r['estimates'][-1] and r['final'] is not r['estimates'][-1]


def test_not_claimed_exact():
    doc = importlib.import_module('sugarcode.extra_doc.kalman_filter186').__doc__
    assert doc.count('NOT_CLAIMED:') == 1
    assert ' '.join(doc[doc.index('NOT_CLAIMED:'):].split()) == (
        'NOT_CLAIMED: this runs one fixed-parameter scalar filter on supplied readings. It does not estimate the '
        'noise variances, test that the model fits, smooth backward, handle several dimensions, or say the estimate '
        'is correct.')


def test_oracle():
    rg = random.Random(67)
    for _ in range(3000):
        zs = [rg.randint(-100, 100) for _ in range(rg.randint(1, 6))]
        m0, p0, q, r = rg.randint(-100, 100), rg.randint(0, 100), rg.randint(0, 20), rg.randint(1, 20)
        keep = zs[:]
        assert kalman_filter(zs, m0, p0, q, r) == oracle(zs, m0, p0, q, r)
        assert zs == keep
    for zs in itertools.product((-5, 0, 7), repeat=3):
        for p0, q, r in itertools.product((0, 1, 5), (0, 2), (1, 3)):
            assert kalman_filter(list(zs), 1, p0, q, r) == oracle(zs, 1, p0, q, r)


def test_errors():
    kalman_filter([100] * 6, -100, 100, 20, 20)
    kalman_filter([-100], 100, 0, 0, 1)
    for bad in (L([1]), (1,), None, 'a'):
        with pytest.raises(T, match='^zs must be a list$'):
            kalman_filter(bad, 0, 0, 0, 1)
    for bad in ([], [1] * 7):
        with pytest.raises(V, match='^zs must hold 1 to 6 entries$'):
            kalman_filter(bad, 0, 0, 0, 1)
    for bad in (True, 1.0, I(1), '1', None):
        with pytest.raises(T, match='^reading 2 must be an exact int$'):
            kalman_filter([1, bad], 0, 0, 0, 1)
        with pytest.raises(T, match='^m0 must be an exact int$'):
            kalman_filter([1], bad, 0, 0, 1)
        with pytest.raises(T, match='^p0 must be an exact int$'):
            kalman_filter([1], 0, bad, 0, 1)
        with pytest.raises(T, match='^q must be an exact int$'):
            kalman_filter([1], 0, 0, bad, 1)
        with pytest.raises(T, match='^r must be an exact int$'):
            kalman_filter([1], 0, 0, 0, bad)
    for bad in (-101, 101):
        with pytest.raises(V, match='^reading 1 must be -100 to 100$'):
            kalman_filter([bad], 0, 0, 0, 1)
        with pytest.raises(V, match='^m0 must be -100 to 100$'):
            kalman_filter([1], bad, 0, 0, 1)
    for bad in (-1, 101):
        with pytest.raises(V, match='^p0 must be 0 to 100$'):
            kalman_filter([1], 0, bad, 0, 1)
    for bad in (-1, 21):
        with pytest.raises(V, match='^q must be 0 to 20$'):
            kalman_filter([1], 0, 0, bad, 1)
    for bad in (0, 21):
        with pytest.raises(V, match='^r must be 1 to 20$'):
            kalman_filter([1], 0, 0, 0, bad)


def test_argument_order():
    with pytest.raises(T, match='^zs must be a list$'):
        kalman_filter('a', 'b', 'c', 'd', 'e')
    with pytest.raises(V, match='^zs must hold'):
        kalman_filter([], 'b', 'c', 'd', 'e')
    with pytest.raises(T, match='^reading 1 must be an exact int$'):
        kalman_filter(['a'], 'b', 'c', 'd', 'e')
    with pytest.raises(V, match='^reading 1 must be -100 to 100$'):
        kalman_filter([999], 'b', 'c', 'd', 'e')
    with pytest.raises(T, match='^m0 must be an exact int$'):
        kalman_filter([1], 'b', 'c', 'd', 'e')
    with pytest.raises(V, match='^m0 must be -100 to 100$'):
        kalman_filter([1], 999, 'c', 'd', 'e')
    with pytest.raises(T, match='^p0 must be an exact int$'):
        kalman_filter([1], 0, 'c', 'd', 'e')
    with pytest.raises(V, match='^p0 must be 0 to 100$'):
        kalman_filter([1], 0, 999, 'd', 'e')
    with pytest.raises(T, match='^q must be an exact int$'):
        kalman_filter([1], 0, 0, 'd', 'e')
    with pytest.raises(V, match='^q must be 0 to 20$'):
        kalman_filter([1], 0, 0, 99, 'e')
    with pytest.raises(T, match='^r must be an exact int$'):
        kalman_filter([1], 0, 0, 0, 'e')


def test_cross_element_first_bad_order():
    for n in (2, 3, 4, 6):
        for i in range(n):
            for j in range(i + 1, n):
                for (e, ee), (l, le) in ((('a', T), (999, V)), ((999, V), ('a', T))):
                    zs = [1] * n
                    zs[i], zs[j] = e, l
                    pat = 'must be an exact int' if ee is T else 'must be -100 to 100'
                    with pytest.raises(ee, match='^reading %d %s$' % (i + 1, pat)):
                        kalman_filter(zs, 'x', 'y', 'z', 'w')
