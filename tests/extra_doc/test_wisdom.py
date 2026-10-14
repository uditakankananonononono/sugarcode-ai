import random
import pytest
from sugarcode.extra_doc.wisdom import check_decisions as ck

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(items):
    # written from the stated rule: under 2 horizons is short-sighted; under 1 lesson is uninformed
    probs = []
    for i, (_, a, b) in enumerate(items):
        if a < 2:
            probs.append((i, 'short_sighted'))
        if b < 1:
            probs.append((i, 'uninformed'))
    return {'problems': sorted(probs), 'decisions': sorted({x for x, _, _ in items}), 'total': len(items)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied decision numbers against two judgment bars. It does not say anyone is wise, that 2 horizons or 1 lesson are the right bars, or that any decision works out. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.wisdom as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'decisions': [], 'total': 0}
    assert ck([('a', 3, 2)]) == {'problems': [], 'decisions': ['a'], 'total': 1}
    assert ck([('a', 1, 2)])['problems'] == [(0, 'short_sighted')]
    assert ck([('a', 0, 2)])['problems'] == [(0, 'short_sighted')]
    assert ck([('a', 3, 0)])['problems'] == [(0, 'uninformed')]
    assert ck([('a', 3, 0)])['problems'] == [(0, 'uninformed')]
    assert ck([('a', 1, 0)])['problems'] == [(0, 'short_sighted'), (0, 'uninformed')]
    assert ck([('a', 1, 0), ('b', 3, 2), ('c', 0, 2)])['problems'] == [
        (0, 'short_sighted'), (0, 'uninformed'), (2, 'short_sighted')]
    assert ck([('b', 3, 2), ('a', 3, 2)]) == {'problems': [], 'decisions': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(7940 + part)
    seen, clean = set(), 0
    for _ in range(60):
        items = []
        for _ in range(rnd.randint(0, 9)):
            items.append((rnd.choice(('x1', 'x2', 'x3')),
                          rnd.choice((0, 1, 2, 10, rnd.randint(0, 10))),
                          rnd.choice((0, 1, 50, rnd.randint(0, 50)))))
        r = ck(items)
        assert r == oracle(items)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'short_sighted', 'uninformed'} and clean >= 2


def test_limits_accepted():
    items = [('x%02d' % k, 3, 2) for k in range(40)]
    r = ck(items)
    assert r['total'] == 40 and r['problems'] == []
    ck([('a' * 24, 10, 50)])
    ck([('a', 0, 0)])


def err(exc, msg, items):
    with pytest.raises(exc) as e:
        ck(items)
    assert str(e.value) == msg


NM = 'decision must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')
PL = 'decisions must be an exact list'
CNT = 'decision count must be at most 40'
TUP = 'each decision must be an exact tuple'
IT3 = 'each decision must have 3 items'
NSS = 'decision must be an exact string'
FA = 'horizons'
FB = 'lessons'


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, PL, bad)
    err(V, CNT, [('x', 3, 2)] * 41)
    for bad in (None, ['x', 3, 2], 'ab', TupleSub(('x', 3, 2)), 5):
        err(T, TUP, [bad])
    for bad in ((), ('x', 3), ('x', 3, 2, 0)):
        err(V, IT3, [bad])
    for bad in NS:
        err(T, NSS, [(bad, 3, 2)])
    for bad in BAD:
        err(V, NM, [(bad, 3, 2)])
    for bad in NI:
        err(T, FA + ' must be an exact integer', [('x', bad, 2)])
        err(T, FB + ' must be an exact integer', [('x', 3, bad)])
    for bad in (-1, 11, -100, 10**9):
        err(V, FA + ' must be 0 to 10', [('x', bad, 2)])
    for bad in (-1, 51, -100, 10**9):
        err(V, FB + ' must be 0 to 50', [('x', 3, bad)])


def _order(err):
    err(T, PL, 'x')
    err(V, CNT, [None] * 41)
    err(T, TUP, [None, ('x',)])
    err(V, IT3, [('x',), None])
    err(T, NSS, [(5, -1, -1)])
    err(V, NM, [('A', -1, -1)])
    err(T, FA + ' must be an exact integer', [('x', '0', -1)])
    err(V, FA + ' must be 0 to 10', [('x', -1, -1)])
    err(T, FB + ' must be an exact integer', [('x', 0, '0')])
    err(V, FB + ' must be 0 to 50', [('x', 0, -1)])
    err(T, NSS, [('x', 3, 2), (5, 3, 2)])
    err(T, FA + ' must be an exact integer', [('x', 3, 2), ('x', '0', 2)])
    err(T, FB + ' must be an exact integer', [('x', 3, 2), ('x', 3, '0')])


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
