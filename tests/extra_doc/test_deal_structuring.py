import random
import pytest
from sugarcode.extra_doc.deal_structuring import check_tranches as ct

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(tranches):
    # written from the stated rule: running sum over 100 is over_full; a zero tranche is empty
    probs = []
    running = 0
    for i, (_, p) in enumerate(tranches):
        running += p
        if running > 100:
            probs.append((i, 'over_full'))
        if p == 0:
            probs.append((i, 'empty'))
    return {'problems': sorted(probs), 'tranches': sorted({t for t, _ in tranches}),
            'funded': sum(p for _, p in tranches), 'total': len(tranches)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied tranche shares against one sum bar. It does not say the '
              'agreement is designed well, that 100 is the right total, or that any payment was made. No '
              'clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.deal_structuring as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ct([]) == {'problems': [], 'tranches': [], 'funded': 0, 'total': 0}
    assert ct([('a', 100)]) == {'problems': [], 'tranches': ['a'], 'funded': 100, 'total': 1}
    assert ct([('a', 60), ('b', 40)])['funded'] == 100
    assert ct([('a', 60), ('b', 40)])['problems'] == []
    assert ct([('a', 60), ('b', 41)])['problems'] == [(1, 'over_full')]
    assert ct([('a', 99), ('b', 1)])['problems'] == []
    assert ct([('a', 0)])['problems'] == [(0, 'empty')]
    assert ct([('a', 100), ('b', 0)])['problems'] == [(1, 'empty')]
    assert ct([('a', 100), ('b', 1)])['problems'] == [(1, 'over_full')]
    assert ct([('a', 60), ('b', 50), ('c', 10)])['problems'] == [(1, 'over_full'), (2, 'over_full')]
    assert ct([('a', 0), ('b', 100)])['problems'] == [(0, 'empty')]
    assert ct([('a', 30), ('b', 30), ('c', 30)])['funded'] == 90
    assert ct([('b', 10), ('a', 10)]) == {'problems': [], 'tranches': ['a', 'b'], 'funded': 20, 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4330 + part)
    seen, clean = set(), 0
    for _ in range(60):
        tranches = []
        for _ in range(rnd.randint(0, 9)):
            tranches.append((rnd.choice(('t1', 't2', 't3')),
                             rnd.choice((0, 1, 40, 60, 100, rnd.randint(0, 100)))))
        r = ct(tranches)
        assert r == oracle(tranches)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'over_full', 'empty'} and clean >= 2


def test_limits_accepted():
    tranches = [('t%02d' % k, 2) for k in range(40)]
    r = ct(tranches)
    assert r['total'] == 40 and r['problems'] == [] and r['funded'] == 80
    ct([('a' * 24, 100)])
    ct([('a', 0)])


def err(exc, msg, tranches):
    with pytest.raises(exc) as e:
        ct(tranches)
    assert str(e.value) == msg


TM = 'tranche must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'tranches must be an exact list', bad)
    err(V, 'tranche count must be at most 40', [('t', 1)] * 41)
    for bad in (None, ['t', 1], 'ab', TupleSub(('t', 1)), 5):
        err(T, 'each tranche must be an exact tuple', [bad])
    for bad in ((), ('t',), ('t', 1, 0)):
        err(V, 'each tranche must have 2 items', [bad])
    for bad in NS:
        err(T, 'tranche must be an exact string', [(bad, 1)])
    for bad in BAD:
        err(V, TM, [(bad, 1)])
    for bad in NI:
        err(T, 'percent must be an exact integer', [('t', bad)])
    for bad in (-1, 101, -100, 10**9):
        err(V, 'percent must be 0 to 100', [('t', bad)])


def _order(err):
    err(T, 'tranches must be an exact list', 'x')
    err(V, 'tranche count must be at most 40', [None] * 41)
    err(T, 'each tranche must be an exact tuple', [None, ('t',)])
    err(V, 'each tranche must have 2 items', [('t',), None])
    err(T, 'tranche must be an exact string', [(5, -1)])
    err(V, TM, [('A', -1)])
    err(T, 'percent must be an exact integer', [('t', '0')])
    err(V, 'percent must be 0 to 100', [('t', -1)])
    err(T, 'tranche must be an exact string', [('t', 1), (5, 1)])
    err(T, 'percent must be an exact integer', [('t', 1), ('t', '0')])


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
