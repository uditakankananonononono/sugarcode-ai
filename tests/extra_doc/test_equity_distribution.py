import random
import pytest
from sugarcode.extra_doc.equity_distribution import check_holders as ck

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(holders):
    # written from the stated rule: over 50 percent is outsized; under 6 cliff months is short
    probs = []
    for i, (_, a, b) in enumerate(holders):
        if a > 50:
            probs.append((i, 'outsized'))
        if b < 6:
            probs.append((i, 'short_cliff'))
    return {'problems': sorted(probs), 'holders': sorted({x for x, _, _ in holders}), 'total': len(holders)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied allocation numbers against two ownership bars. It does not say '
              'ownership is allocated well, that 50 percent or 6 months are the right bars, or that any vesting '
              'happens. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.equity_distribution as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'holders': [], 'total': 0}
    assert ck([('a', 50, 6)]) == {'problems': [], 'holders': ['a'], 'total': 1}
    assert ck([('a', 51, 6)])['problems'] == [(0, 'outsized')]
    assert ck([('a', 100, 6)])['problems'] == [(0, 'outsized')]
    assert ck([('a', 0, 6)])['problems'] == []
    assert ck([('a', 50, 5)])['problems'] == [(0, 'short_cliff')]
    assert ck([('a', 50, 0)])['problems'] == [(0, 'short_cliff')]
    assert ck([('a', 51, 5)])['problems'] == [(0, 'outsized'), (0, 'short_cliff')]
    assert ck([('a', 51, 5), ('b', 20, 12), ('c', 100, 24)])['problems'] == [
        (0, 'outsized'), (0, 'short_cliff'), (2, 'outsized')]
    assert ck([('b', 20, 12), ('a', 20, 12)]) == {'problems': [], 'holders': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4960 + part)
    seen, clean = set(), 0
    for _ in range(60):
        holders = []
        for _ in range(rnd.randint(0, 9)):
            holders.append((rnd.choice(('x1', 'x2', 'x3')),
                            rnd.choice((0, 50, 51, 100, rnd.randint(0, 100))),
                            rnd.choice((0, 5, 6, 24, rnd.randint(0, 24)))))
        r = ck(holders)
        assert r == oracle(holders)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'outsized', 'short_cliff'} and clean >= 2


def test_limits_accepted():
    holders = [('x%02d' % k, 20, 12) for k in range(40)]
    r = ck(holders)
    assert r['total'] == 40 and r['problems'] == []
    ck([('a' * 24, 100, 24)])
    ck([('a', 0, 0)])


def err(exc, msg, holders):
    with pytest.raises(exc) as e:
        ck(holders)
    assert str(e.value) == msg


NM = 'holder must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'holders must be an exact list', bad)
    err(V, 'holder count must be at most 40', [('x', 20, 12)] * 41)
    for bad in (None, ['x', 20, 12], 'ab', TupleSub(('x', 20, 12)), 5):
        err(T, 'each holder must be an exact tuple', [bad])
    for bad in ((), ('x', 20), ('x', 20, 12, 0)):
        err(V, 'each holder must have 3 items', [bad])
    for bad in NS:
        err(T, 'holder must be an exact string', [(bad, 20, 12)])
    for bad in BAD:
        err(V, NM, [(bad, 20, 12)])
    for bad in NI:
        err(T, 'percent must be an exact integer', [('x', bad, 12)])
        err(T, 'cliff_months must be an exact integer', [('x', 20, bad)])
    for bad in (-1, 101, -100, 10**9):
        err(V, 'percent must be 0 to 100', [('x', bad, 12)])
    for bad in (-1, 25, -100, 10**9):
        err(V, 'cliff_months must be 0 to 24', [('x', 20, bad)])


def _order(err):
    err(T, 'holders must be an exact list', 'x')
    err(V, 'holder count must be at most 40', [None] * 41)
    err(T, 'each holder must be an exact tuple', [None, ('x',)])
    err(V, 'each holder must have 3 items', [('x',), None])
    err(T, 'holder must be an exact string', [(5, -1, -1)])
    err(V, NM, [('A', -1, -1)])
    err(T, 'percent must be an exact integer', [('x', '0', -1)])
    err(V, 'percent must be 0 to 100', [('x', -1, -1)])
    err(T, 'cliff_months must be an exact integer', [('x', 0, '0')])
    err(V, 'cliff_months must be 0 to 24', [('x', 0, -1)])
    err(T, 'holder must be an exact string', [('x', 20, 12), (5, 20, 12)])
    err(T, 'percent must be an exact integer', [('x', 20, 12), ('x', '0', 12)])
    err(T, 'cliff_months must be an exact integer', [('x', 20, 12), ('x', 20, '0')])


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
