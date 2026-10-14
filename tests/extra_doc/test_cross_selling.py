import random
import pytest
from sugarcode.extra_doc.cross_selling import check_pairs as cp

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(pairs):
    # written from the stated rule: anchor equal to addon is a self pair; lift under 5 is weak
    probs = []
    for i, (a, d, l) in enumerate(pairs):
        if a == d:
            probs.append((i, 'self_pair'))
        if l < 5:
            probs.append((i, 'weak_pair'))
    products = set()
    for a, d, _ in pairs:
        products.add(a)
        products.add(d)
    return {'problems': sorted(probs), 'products': sorted(products), 'total': len(pairs)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied pairs against two fit bars. It does not say the pairs sell '
              'complementary products, that 5 percent is the right lift bar, or that any basket grew. No '
              'clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.cross_selling as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert cp([]) == {'problems': [], 'products': [], 'total': 0}
    assert cp([('a', 'b', 5)]) == {'problems': [], 'products': ['a', 'b'], 'total': 1}
    assert cp([('a', 'b', 1000)])['problems'] == []
    assert cp([('a', 'a', 50)])['problems'] == [(0, 'self_pair')]
    assert cp([('a', 'b', 4)])['problems'] == [(0, 'weak_pair')]
    assert cp([('a', 'b', 0)])['problems'] == [(0, 'weak_pair')]
    assert cp([('a', 'b', -100)])['problems'] == [(0, 'weak_pair')]
    assert cp([('a', 'a', 0)])['problems'] == [(0, 'self_pair'), (0, 'weak_pair')]
    assert cp([('a', 'b', 6), ('b', 'a', 4)])['problems'] == [(1, 'weak_pair')]
    assert cp([('b', 'c', 10), ('a', 'b', 10)]) == {'problems': [], 'products': ['a', 'b', 'c'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4440 + part)
    seen, clean = set(), 0
    for _ in range(60):
        pairs = []
        for _ in range(rnd.randint(0, 9)):
            pairs.append((rnd.choice(('a1', 'a2')), rnd.choice(('a1', 'b1', 'b2')),
                          rnd.choice((-100, 0, 4, 5, 1000, rnd.randint(-100, 1000)))))
        r = cp(pairs)
        assert r == oracle(pairs)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'self_pair', 'weak_pair'} and clean >= 2


def test_limits_accepted():
    pairs = [('p%02d' % k, 'q%02d' % k, 10) for k in range(40)]
    r = cp(pairs)
    assert r['total'] == 40 and r['problems'] == []
    cp([('a' * 24, 'b' * 24, 1000)])
    cp([('a', 'b', -100)])


def err(exc, msg, pairs):
    with pytest.raises(exc) as e:
        cp(pairs)
    assert str(e.value) == msg


AM = 'anchor must be 1 to 24 lowercase identifier characters'
DM = 'addon must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'pairs must be an exact list', bad)
    err(V, 'pair count must be at most 40', [('a', 'b', 5)] * 41)
    for bad in (None, ['a', 'b', 5], 'ab', TupleSub(('a', 'b', 5)), 5):
        err(T, 'each pair must be an exact tuple', [bad])
    for bad in ((), ('a', 'b'), ('a', 'b', 5, 0)):
        err(V, 'each pair must have 3 items', [bad])
    for bad in NS:
        err(T, 'anchor must be an exact string', [(bad, 'b', 5)])
        err(T, 'addon must be an exact string', [('a', bad, 5)])
    for bad in BAD:
        err(V, AM, [(bad, 'b', 5)])
        err(V, DM, [('a', bad, 5)])
    for bad in NI:
        err(T, 'lift must be an exact integer', [('a', 'b', bad)])
    for bad in (-101, 1001, -1000, 10**9):
        err(V, 'lift must be -100 to 1000', [('a', 'b', bad)])


def _order(err):
    err(T, 'pairs must be an exact list', 'x')
    err(V, 'pair count must be at most 40', [None] * 41)
    err(T, 'each pair must be an exact tuple', [None, ('a',)])
    err(V, 'each pair must have 3 items', [('a',), None])
    err(T, 'anchor must be an exact string', [(5, 'b', 0)])
    err(V, AM, [('A', 'b', 0)])
    err(T, 'addon must be an exact string', [('a', 5, 0)])
    err(V, DM, [('a', 'B', 0)])
    err(T, 'lift must be an exact integer', [('a', 'b', '5')])
    err(V, 'lift must be -100 to 1000', [('a', 'b', 1001)])
    err(T, 'anchor must be an exact string', [('a', 'b', 5), (5, 'b', 5)])
    err(T, 'addon must be an exact string', [('a', 'b', 5), ('a', 5, 5)])
    err(T, 'lift must be an exact integer', [('a', 'b', 5), ('a', 'b', '5')])


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
