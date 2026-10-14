import random
import pytest
from sugarcode.extra_doc.tolerance import check_disagreements as ck

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
    # written from the stated rule: over 3 interruptions is dismissive; under 2 viewpoints leaves a side unheard
    probs = []
    for i, (_, a, b) in enumerate(items):
        if a > 3:
            probs.append((i, 'dismissive'))
        if b < 2:
            probs.append((i, 'unheard_side'))
    return {'problems': sorted(probs), 'disagreements': sorted({x for x, _, _ in items}), 'total': len(items)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied disagreement numbers against two acceptance bars. It does not say anyone is tolerant, that 3 interruptions or 2 viewpoints are the right bars, or that any difference is respected. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.tolerance as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'disagreements': [], 'total': 0}
    assert ck([('a', 1, 3)]) == {'problems': [], 'disagreements': ['a'], 'total': 1}
    assert ck([('a', 4, 3)])['problems'] == [(0, 'dismissive')]
    assert ck([('a', 50, 3)])['problems'] == [(0, 'dismissive')]
    assert ck([('a', 1, 1)])['problems'] == [(0, 'unheard_side')]
    assert ck([('a', 1, 0)])['problems'] == [(0, 'unheard_side')]
    assert ck([('a', 4, 1)])['problems'] == [(0, 'dismissive'), (0, 'unheard_side')]
    assert ck([('a', 4, 1), ('b', 1, 3), ('c', 50, 3)])['problems'] == [
        (0, 'dismissive'), (0, 'unheard_side'), (2, 'dismissive')]
    assert ck([('b', 1, 3), ('a', 1, 3)]) == {'problems': [], 'disagreements': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(7870 + part)
    seen, clean = set(), 0
    for _ in range(60):
        items = []
        for _ in range(rnd.randint(0, 9)):
            items.append((rnd.choice(('x1', 'x2', 'x3')),
                          rnd.choice((0, 3, 4, 50, rnd.randint(0, 50))),
                          rnd.choice((0, 1, 2, 20, rnd.randint(0, 20)))))
        r = ck(items)
        assert r == oracle(items)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'dismissive', 'unheard_side'} and clean >= 2


def test_limits_accepted():
    items = [('x%02d' % k, 1, 3) for k in range(40)]
    r = ck(items)
    assert r['total'] == 40 and r['problems'] == []
    ck([('a' * 24, 50, 20)])
    ck([('a', 0, 0)])


def err(exc, msg, items):
    with pytest.raises(exc) as e:
        ck(items)
    assert str(e.value) == msg


NM = 'disagreement must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')
PL = 'disagreements must be an exact list'
CNT = 'disagreement count must be at most 40'
TUP = 'each disagreement must be an exact tuple'
IT3 = 'each disagreement must have 3 items'
NSS = 'disagreement must be an exact string'
FA = 'interruptions'
FB = 'viewpoints'


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, PL, bad)
    err(V, CNT, [('x', 1, 3)] * 41)
    for bad in (None, ['x', 1, 3], 'ab', TupleSub(('x', 1, 3)), 5):
        err(T, TUP, [bad])
    for bad in ((), ('x', 1), ('x', 1, 3, 0)):
        err(V, IT3, [bad])
    for bad in NS:
        err(T, NSS, [(bad, 1, 3)])
    for bad in BAD:
        err(V, NM, [(bad, 1, 3)])
    for bad in NI:
        err(T, FA + ' must be an exact integer', [('x', bad, 3)])
        err(T, FB + ' must be an exact integer', [('x', 1, bad)])
    for bad in (-1, 51, -100, 10**9):
        err(V, FA + ' must be 0 to 50', [('x', bad, 3)])
    for bad in (-1, 21, -100, 10**9):
        err(V, FB + ' must be 0 to 20', [('x', 1, bad)])


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
    err(T, NSS, [('x', 1, 3), (5, 1, 3)])
    err(T, FA + ' must be an exact integer', [('x', 1, 3), ('x', '0', 3)])
    err(T, FB + ' must be an exact integer', [('x', 1, 3), ('x', 1, '0')])


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
