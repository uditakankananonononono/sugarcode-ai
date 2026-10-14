import random
import pytest
from sugarcode.extra_doc.gratitude import check_weeks as ck

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
    # written from the stated rule: under 2 thanks is unnoticing; over 5 received-only is one-sided
    probs = []
    for i, (_, a, b) in enumerate(items):
        if a < 2:
            probs.append((i, 'unnoticing'))
        if b > 5:
            probs.append((i, 'one_sided'))
    return {'problems': sorted(probs), 'weeks': sorted({x for x, _, _ in items}), 'total': len(items)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied week numbers against two acknowledgment bars. It does not say anyone feels grateful, that 2 thanks or 5 received-only are the right bars, or that any thanks is sincere. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.gratitude as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'weeks': [], 'total': 0}
    assert ck([('a', 4, 2)]) == {'problems': [], 'weeks': ['a'], 'total': 1}
    assert ck([('a', 1, 2)])['problems'] == [(0, 'unnoticing')]
    assert ck([('a', 0, 2)])['problems'] == [(0, 'unnoticing')]
    assert ck([('a', 4, 6)])['problems'] == [(0, 'one_sided')]
    assert ck([('a', 4, 100)])['problems'] == [(0, 'one_sided')]
    assert ck([('a', 1, 6)])['problems'] == [(0, 'one_sided'), (0, 'unnoticing')]
    assert ck([('a', 1, 6), ('b', 4, 2), ('c', 0, 2)])['problems'] == [
        (0, 'one_sided'), (0, 'unnoticing'), (2, 'unnoticing')]
    assert ck([('b', 4, 2), ('a', 4, 2)]) == {'problems': [], 'weeks': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(7890 + part)
    seen, clean = set(), 0
    for _ in range(60):
        items = []
        for _ in range(rnd.randint(0, 9)):
            items.append((rnd.choice(('x1', 'x2', 'x3')),
                          rnd.choice((0, 1, 2, 100, rnd.randint(0, 100))),
                          rnd.choice((0, 5, 6, 100, rnd.randint(0, 100)))))
        r = ck(items)
        assert r == oracle(items)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'unnoticing', 'one_sided'} and clean >= 2


def test_limits_accepted():
    items = [('x%02d' % k, 4, 2) for k in range(40)]
    r = ck(items)
    assert r['total'] == 40 and r['problems'] == []
    ck([('a' * 24, 100, 100)])
    ck([('a', 0, 0)])


def err(exc, msg, items):
    with pytest.raises(exc) as e:
        ck(items)
    assert str(e.value) == msg


NM = 'week must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')
PL = 'weeks must be an exact list'
CNT = 'week count must be at most 40'
TUP = 'each week must be an exact tuple'
IT3 = 'each week must have 3 items'
NSS = 'week must be an exact string'
FA = 'thanks'
FB = 'received_only'


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, PL, bad)
    err(V, CNT, [('x', 4, 2)] * 41)
    for bad in (None, ['x', 4, 2], 'ab', TupleSub(('x', 4, 2)), 5):
        err(T, TUP, [bad])
    for bad in ((), ('x', 4), ('x', 4, 2, 0)):
        err(V, IT3, [bad])
    for bad in NS:
        err(T, NSS, [(bad, 4, 2)])
    for bad in BAD:
        err(V, NM, [(bad, 4, 2)])
    for bad in NI:
        err(T, FA + ' must be an exact integer', [('x', bad, 2)])
        err(T, FB + ' must be an exact integer', [('x', 4, bad)])
    for bad in (-1, 101, -100, 10**9):
        err(V, FA + ' must be 0 to 100', [('x', bad, 2)])
    for bad in (-1, 101, -100, 10**9):
        err(V, FB + ' must be 0 to 100', [('x', 4, bad)])


def _order(err):
    err(T, PL, 'x')
    err(V, CNT, [None] * 41)
    err(T, TUP, [None, ('x',)])
    err(V, IT3, [('x',), None])
    err(T, NSS, [(5, -1, -1)])
    err(V, NM, [('A', -1, -1)])
    err(T, FA + ' must be an exact integer', [('x', '0', -1)])
    err(V, FA + ' must be 0 to 100', [('x', -1, -1)])
    err(T, FB + ' must be an exact integer', [('x', 0, '0')])
    err(V, FB + ' must be 0 to 100', [('x', 0, -1)])
    err(T, NSS, [('x', 4, 2), (5, 4, 2)])
    err(T, FA + ' must be an exact integer', [('x', 4, 2), ('x', '0', 2)])
    err(T, FB + ' must be an exact integer', [('x', 4, 2), ('x', 4, '0')])


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
