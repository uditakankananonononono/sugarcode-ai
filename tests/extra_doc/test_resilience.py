import random
import pytest
from sugarcode.extra_doc.resilience import check_setbacks as ck

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
    # written from the stated rule: under 1 recovery is staying down; over 2 consecutive quits is brittle
    probs = []
    for i, (_, a, b) in enumerate(items):
        if a < 1:
            probs.append((i, 'staying_down'))
        if b > 2:
            probs.append((i, 'brittle'))
    return {'problems': sorted(probs), 'setbacks': sorted({x for x, _, _ in items}), 'total': len(items)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied setback numbers against two recovery bars. It does not say anyone bounces back, that 1 recovery or 2 quits are the right bars, or that any setback is overcome. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.resilience as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'setbacks': [], 'total': 0}
    assert ck([('a', 2, 1)]) == {'problems': [], 'setbacks': ['a'], 'total': 1}
    assert ck([('a', 0, 1)])['problems'] == [(0, 'staying_down')]
    assert ck([('a', 0, 1)])['problems'] == [(0, 'staying_down')]
    assert ck([('a', 2, 3)])['problems'] == [(0, 'brittle')]
    assert ck([('a', 2, 20)])['problems'] == [(0, 'brittle')]
    assert ck([('a', 0, 3)])['problems'] == [(0, 'brittle'), (0, 'staying_down')]
    assert ck([('a', 0, 3), ('b', 2, 1), ('c', 0, 1)])['problems'] == [
        (0, 'brittle'), (0, 'staying_down'), (2, 'staying_down')]
    assert ck([('b', 2, 1), ('a', 2, 1)]) == {'problems': [], 'setbacks': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(7980 + part)
    seen, clean = set(), 0
    for _ in range(60):
        items = []
        for _ in range(rnd.randint(0, 9)):
            items.append((rnd.choice(('x1', 'x2', 'x3')),
                          rnd.choice((0, 1, 50, rnd.randint(0, 50))),
                          rnd.choice((0, 2, 3, 20, rnd.randint(0, 20)))))
        r = ck(items)
        assert r == oracle(items)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'staying_down', 'brittle'} and clean >= 2


def test_limits_accepted():
    items = [('x%02d' % k, 2, 1) for k in range(40)]
    r = ck(items)
    assert r['total'] == 40 and r['problems'] == []
    ck([('a' * 24, 50, 20)])
    ck([('a', 0, 0)])


def err(exc, msg, items):
    with pytest.raises(exc) as e:
        ck(items)
    assert str(e.value) == msg


NM = 'setback must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')
PL = 'setbacks must be an exact list'
CNT = 'setback count must be at most 40'
TUP = 'each setback must be an exact tuple'
IT3 = 'each setback must have 3 items'
NSS = 'setback must be an exact string'
FA = 'recoveries'
FB = 'consecutive_quits'


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, PL, bad)
    err(V, CNT, [('x', 2, 1)] * 41)
    for bad in (None, ['x', 2, 1], 'ab', TupleSub(('x', 2, 1)), 5):
        err(T, TUP, [bad])
    for bad in ((), ('x', 2), ('x', 2, 1, 0)):
        err(V, IT3, [bad])
    for bad in NS:
        err(T, NSS, [(bad, 2, 1)])
    for bad in BAD:
        err(V, NM, [(bad, 2, 1)])
    for bad in NI:
        err(T, FA + ' must be an exact integer', [('x', bad, 1)])
        err(T, FB + ' must be an exact integer', [('x', 2, bad)])
    for bad in (-1, 51, -100, 10**9):
        err(V, FA + ' must be 0 to 50', [('x', bad, 1)])
    for bad in (-1, 21, -100, 10**9):
        err(V, FB + ' must be 0 to 20', [('x', 2, bad)])


def _order(err):
    err(T, PL, 'x')
    err(V, CNT, [None] * 41)
    err(T, TUP, [None, ('x',)])
    err(V, IT3, [('x',), None])
    err(T, NSS, [(5, -1, -1)])
    err(V, NM, [('A', -1, -1)])
    err(T, FA + ' must be an exact integer', [('x', '0', -1)])
    err(V, FA + ' must be 0 to 50', [('x', -1, -1)])
    err(T, FB + ' must be an exact integer', [('x', 0, '0')])
    err(V, FB + ' must be 0 to 20', [('x', 0, -1)])
    err(T, NSS, [('x', 2, 1), (5, 2, 1)])
    err(T, FA + ' must be an exact integer', [('x', 2, 1), ('x', '0', 1)])
    err(T, FB + ' must be an exact integer', [('x', 2, 1), ('x', 2, '0')])


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
