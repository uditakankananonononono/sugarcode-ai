import random
import pytest
from sugarcode.extra_doc.pricing_strategy import check_prices as cp

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(prices):
    # written from the stated rule: below cost flags; over five times cost flags, except at zero cost
    probs = []
    for i, (_, c, p) in enumerate(prices):
        if p < c:
            probs.append((i, 'below_cost'))
        if c > 0 and p > 5 * c:
            probs.append((i, 'markup_high'))
    return {'problems': sorted(probs), 'products': sorted({x for x, _, _ in prices}), 'total': len(prices)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied prices against two band bars. It does not say the prices are '
              'optimal, that five times cost is the right cap, or that anything sold. No clinical or wet-lab '
              'claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.pricing_strategy as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert cp([]) == {'problems': [], 'products': [], 'total': 0}
    assert cp([('p', 100, 100)]) == {'problems': [], 'products': ['p'], 'total': 1}
    assert cp([('p', 100, 99)])['problems'] == [(0, 'below_cost')]
    assert cp([('p', 1, 0)])['problems'] == [(0, 'below_cost')]
    assert cp([('p', 100, 500)])['problems'] == []
    assert cp([('p', 100, 501)])['problems'] == [(0, 'markup_high')]
    assert cp([('p', 1, 6)])['problems'] == [(0, 'markup_high')]
    assert cp([('p', 0, 0)])['problems'] == []
    assert cp([('p', 0, 1000000)])['problems'] == []
    assert cp([('p', 1000000, 0)])['problems'] == [(0, 'below_cost')]
    assert cp([('p', 200, 150)])['problems'] == [(0, 'below_cost')]
    assert cp([('a', 200, 150), ('b', 10, 60), ('c', 10, 50)])['problems'] == [
        (0, 'below_cost'), (1, 'markup_high')]
    assert cp([('b', 1, 1), ('a', 1, 1)]) == {'problems': [], 'products': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4340 + part)
    seen, clean = set(), 0
    for _ in range(60):
        prices = []
        for _ in range(rnd.randint(0, 9)):
            prices.append((rnd.choice(('p1', 'p2', 'p3')),
                           rnd.choice((0, 1, 100, 1000000, rnd.randint(0, 1000))),
                           rnd.choice((0, 99, 100, 500, 501, 1000000, rnd.randint(0, 1200)))))
        r = cp(prices)
        assert r == oracle(prices)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'below_cost', 'markup_high'} and clean >= 2


def test_limits_accepted():
    prices = [('p%02d' % k, 100, 200) for k in range(40)]
    r = cp(prices)
    assert r['total'] == 40 and r['problems'] == []
    cp([('a' * 24, 1000000, 1000000)])
    cp([('a', 0, 0)])


def err(exc, msg, prices):
    with pytest.raises(exc) as e:
        cp(prices)
    assert str(e.value) == msg


PM = 'product must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'prices must be an exact list', bad)
    err(V, 'price count must be at most 40', [('p', 0, 0)] * 41)
    for bad in (None, ['p', 0, 0], 'ab', TupleSub(('p', 0, 0)), 5):
        err(T, 'each price must be an exact tuple', [bad])
    for bad in ((), ('p', 0), ('p', 0, 0, 0)):
        err(V, 'each price must have 3 items', [bad])
    for bad in NS:
        err(T, 'product must be an exact string', [(bad, 0, 0)])
    for bad in BAD:
        err(V, PM, [(bad, 0, 0)])
    for bad in NI:
        err(T, 'cost must be an exact integer', [('p', bad, 0)])
        err(T, 'price must be an exact integer', [('p', 0, bad)])
    for bad in (-1, 1000001, -100, 10**9):
        err(V, 'cost must be 0 to 1000000', [('p', bad, 0)])
        err(V, 'price must be 0 to 1000000', [('p', 0, bad)])


def _order(err):
    err(T, 'prices must be an exact list', 'x')
    err(V, 'price count must be at most 40', [None] * 41)
    err(T, 'each price must be an exact tuple', [None, ('p',)])
    err(V, 'each price must have 3 items', [('p',), None])
    err(T, 'product must be an exact string', [(5, -1, -1)])
    err(V, PM, [('A', -1, -1)])
    err(T, 'cost must be an exact integer', [('p', '0', -1)])
    err(V, 'cost must be 0 to 1000000', [('p', -1, -1)])
    err(T, 'price must be an exact integer', [('p', 0, '0')])
    err(V, 'price must be 0 to 1000000', [('p', 0, -1)])
    err(T, 'product must be an exact string', [('p', 0, 0), (5, 0, 0)])
    err(T, 'cost must be an exact integer', [('p', 0, 0), ('p', '0', 0)])
    err(T, 'price must be an exact integer', [('p', 0, 0), ('p', 0, '0')])


def _collect(fn):
    out = []

    def rec(exc, msg, *a):
        out.append((exc, msg) + a)
    fn(rec)
    return out


@pytest.mark.parametrize('exc,msg,t', _collect(_pins))
def test_pin(exc, msg, t):
    err(exc, msg, t)


@pytest.mark.parametrize('exc,msg,t', _collect(_order))
def test_order(exc, msg, t):
    err(exc, msg, t)
