import random
import pytest
from sugarcode.extra_doc.cognitive_enhancement import check_programs as ck

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
    # written from the stated rule: under 1 baseline is unmeasured; under 5 sessions is untrained
    probs = []
    for i, (_, a, b) in enumerate(items):
        if a < 1:
            probs.append((i, 'unmeasured'))
        if b < 5:
            probs.append((i, 'untrained'))
    return {'problems': sorted(probs), 'programs': sorted({x for x, _, _ in items}), 'total': len(items)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied program numbers against two training bars. It does not say cognition improves, that 1 baseline or 5 sessions are the right bars, or that any program works. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.cognitive_enhancement as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'programs': [], 'total': 0}
    assert ck([('a', 2, 10)]) == {'problems': [], 'programs': ['a'], 'total': 1}
    assert ck([('a', 0, 10)])['problems'] == [(0, 'unmeasured')]
    assert ck([('a', 0, 10)])['problems'] == [(0, 'unmeasured')]
    assert ck([('a', 2, 4)])['problems'] == [(0, 'untrained')]
    assert ck([('a', 2, 0)])['problems'] == [(0, 'untrained')]
    assert ck([('a', 0, 4)])['problems'] == [(0, 'unmeasured'), (0, 'untrained')]
    assert ck([('a', 0, 4), ('b', 2, 10), ('c', 0, 10)])['problems'] == [
        (0, 'unmeasured'), (0, 'untrained'), (2, 'unmeasured')]
    assert ck([('b', 2, 10), ('a', 2, 10)]) == {'problems': [], 'programs': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(10070 + part)
    seen, clean = set(), 0
    for _ in range(60):
        items = []
        for _ in range(rnd.randint(0, 9)):
            items.append((rnd.choice(('x1', 'x2', 'x3')),
                          rnd.choice((0, 1, 20, rnd.randint(0, 20))),
                          rnd.choice((0, 4, 5, 1000, rnd.randint(0, 1000)))))
        r = ck(items)
        assert r == oracle(items)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'unmeasured', 'untrained'} and clean >= 2


def test_limits_accepted():
    items = [('x%02d' % k, 2, 10) for k in range(40)]
    r = ck(items)
    assert r['total'] == 40 and r['problems'] == []
    ck([('a' * 24, 20, 1000)])
    ck([('a', 0, 0)])


def err(exc, msg, items):
    with pytest.raises(exc) as e:
        ck(items)
    assert str(e.value) == msg


NM = 'program must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')
PL = 'programs must be an exact list'
CNT = 'program count must be at most 40'
TUP = 'each program must be an exact tuple'
IT3 = 'each program must have 3 items'
NSS = 'program must be an exact string'
FA = 'baselines'
FB = 'sessions'


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, PL, bad)
    err(V, CNT, [('x', 2, 10)] * 41)
    for bad in (None, ['x', 2, 10], 'ab', TupleSub(('x', 2, 10)), 5):
        err(T, TUP, [bad])
    for bad in ((), ('x', 2), ('x', 2, 10, 0)):
        err(V, IT3, [bad])
    for bad in NS:
        err(T, NSS, [(bad, 2, 10)])
    for bad in BAD:
        err(V, NM, [(bad, 2, 10)])
    for bad in NI:
        err(T, FA + ' must be an exact integer', [('x', bad, 10)])
        err(T, FB + ' must be an exact integer', [('x', 2, bad)])
    for bad in (-1, 21, -100, 10**9):
        err(V, FA + ' must be 0 to 20', [('x', bad, 10)])
    for bad in (-1, 1001, -100, 10**9):
        err(V, FB + ' must be 0 to 1000', [('x', 2, bad)])


def _order(err):
    err(T, PL, 'x')
    err(V, CNT, [None] * 41)
    err(T, TUP, [None, ('x',)])
    err(V, IT3, [('x',), None])
    err(T, NSS, [(5, -1, -1)])
    err(V, NM, [('A', -1, -1)])
    err(T, FA + ' must be an exact integer', [('x', '0', -1)])
    err(V, FA + ' must be 0 to 20', [('x', -1, -1)])
    err(T, FB + ' must be an exact integer', [('x', 0, '0')])
    err(V, FB + ' must be 0 to 1000', [('x', 0, -1)])
    err(T, NSS, [('x', 2, 10), (5, 2, 10)])
    err(T, FA + ' must be an exact integer', [('x', 2, 10), ('x', '0', 10)])
    err(T, FB + ' must be an exact integer', [('x', 2, 10), ('x', 2, '0')])


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
    assert ck([('a_b', 2, 10)]) == {'problems': [], 'programs': ['a_b'], 'total': 1}


def test_name_interior_space_rejected():
    err(V, NM, [('a b', 2, 10)])
