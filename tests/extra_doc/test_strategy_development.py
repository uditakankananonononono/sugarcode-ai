import random
import pytest
from sugarcode.extra_doc.strategy_development import check_plans as ck

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(plans):
    # written from the stated rule: under 1 competitive move is inert; under 2 reviews is unchecked
    probs = []
    for i, (_, a, b) in enumerate(plans):
        if a < 1:
            probs.append((i, 'inert'))
        if b < 2:
            probs.append((i, 'unchecked'))
    return {'problems': sorted(probs), 'plans': sorted({x for x, _, _ in plans}), 'total': len(plans)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied plan numbers against two approach bars. It does not say the '
              'approach competes, that 1 move or 2 reviews are the right bars, or that any plan wins. '
              'No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.strategy_development as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'plans': [], 'total': 0}
    assert ck([('a', 1, 2)]) == {'problems': [], 'plans': ['a'], 'total': 1}
    assert ck([('a', 0, 2)])['problems'] == [(0, 'inert')]
    assert ck([('a', 20, 2)])['problems'] == []
    assert ck([('a', 1, 1)])['problems'] == [(0, 'unchecked')]
    assert ck([('a', 1, 0)])['problems'] == [(0, 'unchecked')]
    assert ck([('a', 0, 0)])['problems'] == [(0, 'inert'), (0, 'unchecked')]
    assert ck([('a', 0, 0), ('b', 3, 4), ('c', 20, 12)])['problems'] == [(0, 'inert'), (0, 'unchecked')]
    assert ck([('b', 3, 4), ('a', 3, 4)]) == {'problems': [], 'plans': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4860 + part)
    seen, clean = set(), 0
    for _ in range(60):
        plans = []
        for _ in range(rnd.randint(0, 9)):
            plans.append((rnd.choice(('x1', 'x2', 'x3')),
                          rnd.choice((0, 1, 20, rnd.randint(0, 20))),
                          rnd.choice((0, 1, 2, 12, rnd.randint(0, 12)))))
        r = ck(plans)
        assert r == oracle(plans)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'inert', 'unchecked'} and clean >= 2


def test_limits_accepted():
    plans = [('x%02d' % k, 1, 2) for k in range(40)]
    r = ck(plans)
    assert r['total'] == 40 and r['problems'] == []
    ck([('a' * 24, 20, 12)])
    ck([('a', 0, 0)])


def err(exc, msg, plans):
    with pytest.raises(exc) as e:
        ck(plans)
    assert str(e.value) == msg


NM = 'plan must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'plans must be an exact list', bad)
    err(V, 'plan count must be at most 40', [('x', 5, 5)] * 41)
    for bad in (None, ['x', 5, 5], 'ab', TupleSub(('x', 5, 5)), 5):
        err(T, 'each plan must be an exact tuple', [bad])
    for bad in ((), ('x', 5), ('x', 5, 5, 0)):
        err(V, 'each plan must have 3 items', [bad])
    for bad in NS:
        err(T, 'plan must be an exact string', [(bad, 5, 5)])
    for bad in BAD:
        err(V, NM, [(bad, 5, 5)])
    for bad in NI:
        err(T, 'moves must be an exact integer', [('x', bad, 5)])
        err(T, 'reviews must be an exact integer', [('x', 5, bad)])
    for bad in (-1, 21, -100, 10**9):
        err(V, 'moves must be 0 to 20', [('x', bad, 5)])
    for bad in (-1, 13, -100, 10**9):
        err(V, 'reviews must be 0 to 12', [('x', 5, bad)])


def _order(err):
    err(T, 'plans must be an exact list', 'x')
    err(V, 'plan count must be at most 40', [None] * 41)
    err(T, 'each plan must be an exact tuple', [None, ('x',)])
    err(V, 'each plan must have 3 items', [('x',), None])
    err(T, 'plan must be an exact string', [(5, -1, -1)])
    err(V, NM, [('A', -1, -1)])
    err(T, 'moves must be an exact integer', [('x', '0', -1)])
    err(V, 'moves must be 0 to 20', [('x', -1, -1)])
    err(T, 'reviews must be an exact integer', [('x', 0, '0')])
    err(V, 'reviews must be 0 to 12', [('x', 0, -1)])
    err(T, 'plan must be an exact string', [('x', 5, 5), (5, 5, 5)])
    err(T, 'moves must be an exact integer', [('x', 5, 5), ('x', '0', 5)])
    err(T, 'reviews must be an exact integer', [('x', 5, 5), ('x', 5, '0')])


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
