import random
import pytest
from sugarcode.extra_doc.nootropics import check_regimens as ck

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
    # written from the stated rule: under 7 logs is untracked; any unchecked interaction is a failed stack check
    probs = []
    for i, (_, a, b) in enumerate(items):
        if a < 7:
            probs.append((i, 'untracked'))
        if b > 0:
            probs.append((i, 'unstacked_check'))
    return {'problems': sorted(probs), 'regimens': sorted({x for x, _, _ in items}), 'total': len(items)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied regimen numbers against two tracking bars. It does not say any substance is safe or effective, that 7 logs or 0 unchecked interactions are the right bars, or that anyone should take anything. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.nootropics as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'regimens': [], 'total': 0}
    assert ck([('a', 14, 0)]) == {'problems': [], 'regimens': ['a'], 'total': 1}
    assert ck([('a', 6, 0)])['problems'] == [(0, 'untracked')]
    assert ck([('a', 0, 0)])['problems'] == [(0, 'untracked')]
    assert ck([('a', 14, 1)])['problems'] == [(0, 'unstacked_check')]
    assert ck([('a', 14, 50)])['problems'] == [(0, 'unstacked_check')]
    assert ck([('a', 6, 1)])['problems'] == [(0, 'unstacked_check'), (0, 'untracked')]
    assert ck([('a', 6, 1), ('b', 14, 0), ('c', 0, 0)])['problems'] == [
        (0, 'unstacked_check'), (0, 'untracked'), (2, 'untracked')]
    assert ck([('b', 14, 0), ('a', 14, 0)]) == {'problems': [], 'regimens': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(10080 + part)
    seen, clean = set(), 0
    for _ in range(60):
        items = []
        for _ in range(rnd.randint(0, 9)):
            items.append((rnd.choice(('x1', 'x2', 'x3')),
                          rnd.choice((0, 6, 7, 365, rnd.randint(0, 365))),
                          rnd.choice((0, 1, 50, rnd.randint(0, 50)))))
        r = ck(items)
        assert r == oracle(items)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'untracked', 'unstacked_check'} and clean >= 2


def test_limits_accepted():
    items = [('x%02d' % k, 14, 0) for k in range(40)]
    r = ck(items)
    assert r['total'] == 40 and r['problems'] == []
    ck([('a' * 24, 365, 50)])
    ck([('a', 0, 0)])


def err(exc, msg, items):
    with pytest.raises(exc) as e:
        ck(items)
    assert str(e.value) == msg


NM = 'regimen must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')
PL = 'regimens must be an exact list'
CNT = 'regimen count must be at most 40'
TUP = 'each regimen must be an exact tuple'
IT3 = 'each regimen must have 3 items'
NSS = 'regimen must be an exact string'
FA = 'logs'
FB = 'interactions_unchecked'


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, PL, bad)
    err(V, CNT, [('x', 14, 0)] * 41)
    for bad in (None, ['x', 14, 0], 'ab', TupleSub(('x', 14, 0)), 5):
        err(T, TUP, [bad])
    for bad in ((), ('x', 14), ('x', 14, 0, 0)):
        err(V, IT3, [bad])
    for bad in NS:
        err(T, NSS, [(bad, 14, 0)])
    for bad in BAD:
        err(V, NM, [(bad, 14, 0)])
    for bad in NI:
        err(T, FA + ' must be an exact integer', [('x', bad, 0)])
        err(T, FB + ' must be an exact integer', [('x', 14, bad)])
    for bad in (-1, 366, -100, 10**9):
        err(V, FA + ' must be 0 to 365', [('x', bad, 0)])
    for bad in (-1, 51, -100, 10**9):
        err(V, FB + ' must be 0 to 50', [('x', 14, bad)])


def _order(err):
    err(T, PL, 'x')
    err(V, CNT, [None] * 41)
    err(T, TUP, [None, ('x',)])
    err(V, IT3, [('x',), None])
    err(T, NSS, [(5, -1, -1)])
    err(V, NM, [('A', -1, -1)])
    err(T, FA + ' must be an exact integer', [('x', '0', -1)])
    err(V, FA + ' must be 0 to 365', [('x', -1, -1)])
    err(T, FB + ' must be an exact integer', [('x', 0, '0')])
    err(V, FB + ' must be 0 to 50', [('x', 0, -1)])
    err(T, NSS, [('x', 14, 0), (5, 14, 0)])
    err(T, FA + ' must be an exact integer', [('x', 14, 0), ('x', '0', 0)])
    err(T, FB + ' must be an exact integer', [('x', 14, 0), ('x', 14, '0')])


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


def test_name_underscore_accepted():
    assert ck([('a_b', 14, 0)]) == {'problems': [], 'regimens': ['a_b'], 'total': 1}


def test_name_interior_space_rejected():
    err(V, NM, [('a b', 14, 0)])
