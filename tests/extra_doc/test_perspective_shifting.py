import random
import pytest
from sugarcode.extra_doc.perspective_shifting import check_analyses as ck

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
    # written from the stated rule: under 2 viewpoints is a fixed view; under 1 reframe is surface
    probs = []
    for i, (_, a, b) in enumerate(items):
        if a < 2:
            probs.append((i, 'fixed_view'))
        if b < 1:
            probs.append((i, 'surface'))
    return {'problems': sorted(probs), 'analyses': sorted({x for x, _, _ in items}), 'total': len(items)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied analysis numbers against two viewpoint bars. It does not say anyone actually shifts perspective, that 2 viewpoints or 1 reframe are the right bars, or that any insight follows. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.perspective_shifting as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'analyses': [], 'total': 0}
    assert ck([('a', 3, 2)]) == {'problems': [], 'analyses': ['a'], 'total': 1}
    assert ck([('a', 1, 2)])['problems'] == [(0, 'fixed_view')]
    assert ck([('a', 0, 2)])['problems'] == [(0, 'fixed_view')]
    assert ck([('a', 3, 0)])['problems'] == [(0, 'surface')]
    assert ck([('a', 3, 0)])['problems'] == [(0, 'surface')]
    assert ck([('a', 1, 0)])['problems'] == [(0, 'fixed_view'), (0, 'surface')]
    assert ck([('a', 1, 0), ('b', 3, 2), ('c', 0, 2)])['problems'] == [
        (0, 'fixed_view'), (0, 'surface'), (2, 'fixed_view')]
    assert ck([('b', 3, 2), ('a', 3, 2)]) == {'problems': [], 'analyses': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(8700 + part)
    seen, clean = set(), 0
    for _ in range(60):
        items = []
        for _ in range(rnd.randint(0, 9)):
            items.append((rnd.choice(('x1', 'x2', 'x3')),
                          rnd.choice((0, 1, 2, 20, rnd.randint(0, 20))),
                          rnd.choice((0, 1, 20, rnd.randint(0, 20)))))
        r = ck(items)
        assert r == oracle(items)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'fixed_view', 'surface'} and clean >= 2


def test_limits_accepted():
    items = [('x%02d' % k, 3, 2) for k in range(40)]
    r = ck(items)
    assert r['total'] == 40 and r['problems'] == []
    ck([('a' * 24, 20, 20)])
    ck([('a', 0, 0)])


def err(exc, msg, items):
    with pytest.raises(exc) as e:
        ck(items)
    assert str(e.value) == msg


NM = 'analysis must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')
PL = 'analyses must be an exact list'
CNT = 'analysis count must be at most 40'
TUP = 'each analysis must be an exact tuple'
IT3 = 'each analysis must have 3 items'
NSS = 'analysis must be an exact string'
FA = 'viewpoints'
FB = 'reframes'


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
    for bad in (-1, 21, -100, 10**9):
        err(V, FA + ' must be 0 to 20', [('x', bad, 2)])
    for bad in (-1, 21, -100, 10**9):
        err(V, FB + ' must be 0 to 20', [('x', 3, bad)])


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
    err(V, FB + ' must be 0 to 20', [('x', 0, -1)])
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
