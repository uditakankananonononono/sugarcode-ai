import random
import pytest
from sugarcode.extra_doc.upselling import check_offers as co

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(offers):
    # written from the stated rule: target must top current; over triple a nonzero current is too steep
    probs = []
    for i, (_, c, t) in enumerate(offers):
        if t <= c:
            probs.append((i, 'no_upgrade'))
        if c > 0 and t > 3 * c:
            probs.append((i, 'too_steep'))
    return {'problems': sorted(probs), 'offers': sorted({o for o, _, _ in offers}), 'total': len(offers)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied offers against two step bars. It does not say the offers '
              'increase order value, that triple is the right step, or that any customer accepted. No clinical '
              'or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.upselling as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert co([]) == {'problems': [], 'offers': [], 'total': 0}
    assert co([('o', 100, 101)]) == {'problems': [], 'offers': ['o'], 'total': 1}
    assert co([('o', 100, 100)])['problems'] == [(0, 'no_upgrade')]
    assert co([('o', 100, 99)])['problems'] == [(0, 'no_upgrade')]
    assert co([('o', 100, 300)])['problems'] == []
    assert co([('o', 100, 301)])['problems'] == [(0, 'too_steep')]
    assert co([('o', 1, 4)])['problems'] == [(0, 'too_steep')]
    assert co([('o', 1, 3)])['problems'] == []
    assert co([('o', 0, 0)])['problems'] == [(0, 'no_upgrade')]
    assert co([('o', 0, 1000000)])['problems'] == []
    assert co([('o', 1000000, 1000000)])['problems'] == [(0, 'no_upgrade')]
    assert co([('a', 50, 50), ('b', 10, 40), ('c', 10, 30)])['problems'] == [
        (0, 'no_upgrade'), (1, 'too_steep')]
    assert co([('b', 1, 2), ('a', 1, 2)]) == {'problems': [], 'offers': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4430 + part)
    seen, clean = set(), 0
    for _ in range(60):
        offers = []
        for _ in range(rnd.randint(0, 9)):
            offers.append((rnd.choice(('o1', 'o2', 'o3')),
                           rnd.choice((0, 1, 100, 1000000, rnd.randint(0, 1000))),
                           rnd.choice((0, 99, 100, 300, 301, 1000000, rnd.randint(0, 1200)))))
        r = co(offers)
        assert r == oracle(offers)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'no_upgrade', 'too_steep'} and clean >= 2


def test_limits_accepted():
    offers = [('o%02d' % k, 100, 150) for k in range(40)]
    r = co(offers)
    assert r['total'] == 40 and r['problems'] == []
    co([('a' * 24, 1000000, 1000000)])
    co([('a', 0, 0)])


def err(exc, msg, offers):
    with pytest.raises(exc) as e:
        co(offers)
    assert str(e.value) == msg


OM = 'offer must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'offers must be an exact list', bad)
    err(V, 'offer count must be at most 40', [('o', 0, 0)] * 41)
    for bad in (None, ['o', 0, 0], 'ab', TupleSub(('o', 0, 0)), 5):
        err(T, 'each offer must be an exact tuple', [bad])
    for bad in ((), ('o', 0), ('o', 0, 0, 0)):
        err(V, 'each offer must have 3 items', [bad])
    for bad in NS:
        err(T, 'offer must be an exact string', [(bad, 0, 0)])
    for bad in BAD:
        err(V, OM, [(bad, 0, 0)])
    for bad in NI:
        err(T, 'current_cents must be an exact integer', [('o', bad, 0)])
        err(T, 'target_cents must be an exact integer', [('o', 0, bad)])
    for bad in (-1, 1000001, -100, 10**9):
        err(V, 'current_cents must be 0 to 1000000', [('o', bad, 0)])
        err(V, 'target_cents must be 0 to 1000000', [('o', 0, bad)])


def _order(err):
    err(T, 'offers must be an exact list', 'x')
    err(V, 'offer count must be at most 40', [None] * 41)
    err(T, 'each offer must be an exact tuple', [None, ('o',)])
    err(V, 'each offer must have 3 items', [('o',), None])
    err(T, 'offer must be an exact string', [(5, -1, -1)])
    err(V, OM, [('A', -1, -1)])
    err(T, 'current_cents must be an exact integer', [('o', '0', -1)])
    err(V, 'current_cents must be 0 to 1000000', [('o', -1, -1)])
    err(T, 'target_cents must be an exact integer', [('o', 0, '0')])
    err(V, 'target_cents must be 0 to 1000000', [('o', 0, -1)])
    err(T, 'offer must be an exact string', [('o', 0, 0), (5, 0, 0)])
    err(T, 'current_cents must be an exact integer', [('o', 0, 0), ('o', '0', 0)])
    err(T, 'target_cents must be an exact integer', [('o', 0, 0), ('o', 0, '0')])


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
