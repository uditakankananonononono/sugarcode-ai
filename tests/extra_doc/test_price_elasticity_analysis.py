import random
import pytest
from sugarcode.extra_doc.price_elasticity_analysis import check_moves as cm

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(moves):
    # written from the stated rule: both nonzero with the same sign is same_sign; flat price with moved demand
    probs = []
    for i, (_, p, d) in enumerate(moves):
        if p != 0 and d != 0 and (p > 0) == (d > 0):
            probs.append((i, 'same_sign'))
        if p == 0 and d != 0:
            probs.append((i, 'phantom_shift'))
    return {'problems': sorted(probs), 'products': sorted({x for x, _, _ in moves}), 'total': len(moves)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied percent changes against two sign rules. It does not measure '
              'elasticity, and it does not say the changes were real or that any customer responded. No clinical '
              'or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.price_elasticity_analysis as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert cm([]) == {'problems': [], 'products': [], 'total': 0}
    assert cm([('p', 10, -5)]) == {'problems': [], 'products': ['p'], 'total': 1}
    assert cm([('p', -10, 5)])['problems'] == []
    assert cm([('p', 10, 5)])['problems'] == [(0, 'same_sign')]
    assert cm([('p', -10, -5)])['problems'] == [(0, 'same_sign')]
    assert cm([('p', 100, 100)])['problems'] == [(0, 'same_sign')]
    assert cm([('p', 1, 2)])['problems'] == [(0, 'same_sign')]
    assert cm([('p', -1, -2)])['problems'] == [(0, 'same_sign')]
    assert cm([('p', 2, -1)])['problems'] == []
    assert cm([('p', -100, 100)])['problems'] == []
    assert cm([('p', 0, 5)])['problems'] == [(0, 'phantom_shift')]
    assert cm([('p', 0, -5)])['problems'] == [(0, 'phantom_shift')]
    assert cm([('p', 0, 0)])['problems'] == []
    assert cm([('p', 5, 0)])['problems'] == []
    assert cm([('a', 1, 1), ('b', 0, 1), ('c', 1, -1)])['problems'] == [(0, 'same_sign'), (1, 'phantom_shift')]
    assert cm([('b', 1, -1), ('a', 1, -1)]) == {'problems': [], 'products': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4350 + part)
    seen, clean = set(), 0
    for _ in range(60):
        moves = []
        for _ in range(rnd.randint(0, 9)):
            moves.append((rnd.choice(('p1', 'p2', 'p3')),
                          rnd.choice((-100, -10, 0, 10, 100, rnd.randint(-100, 100))),
                          rnd.choice((-100, -10, 0, 10, 100, rnd.randint(-100, 100)))))
        r = cm(moves)
        assert r == oracle(moves)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'same_sign', 'phantom_shift'} and clean >= 2


def test_limits_accepted():
    moves = [('p%02d' % k, 10, -10) for k in range(40)]
    r = cm(moves)
    assert r['total'] == 40 and r['problems'] == []
    cm([('a' * 24, -100, 100)])
    cm([('a', 0, 0)])


def err(exc, msg, moves):
    with pytest.raises(exc) as e:
        cm(moves)
    assert str(e.value) == msg


PM = 'product must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'moves must be an exact list', bad)
    err(V, 'move count must be at most 40', [('p', 0, 0)] * 41)
    for bad in (None, ['p', 0, 0], 'ab', TupleSub(('p', 0, 0)), 5):
        err(T, 'each move must be an exact tuple', [bad])
    for bad in ((), ('p', 0), ('p', 0, 0, 0)):
        err(V, 'each move must have 3 items', [bad])
    for bad in NS:
        err(T, 'product must be an exact string', [(bad, 0, 0)])
    for bad in BAD:
        err(V, PM, [(bad, 0, 0)])
    for bad in NI:
        err(T, 'price_delta must be an exact integer', [('p', bad, 0)])
        err(T, 'demand_delta must be an exact integer', [('p', 0, bad)])
    for bad in (-101, 101, -1000, 10**9):
        err(V, 'price_delta must be -100 to 100', [('p', bad, 0)])
        err(V, 'demand_delta must be -100 to 100', [('p', 0, bad)])


def _order(err):
    err(T, 'moves must be an exact list', 'x')
    err(V, 'move count must be at most 40', [None] * 41)
    err(T, 'each move must be an exact tuple', [None, ('p',)])
    err(V, 'each move must have 3 items', [('p',), None])
    err(T, 'product must be an exact string', [(5, 0, 0)])
    err(V, PM, [('A', 0, 0)])
    err(T, 'price_delta must be an exact integer', [('p', '0', 0)])
    err(V, 'price_delta must be -100 to 100', [('p', 101, 0)])
    err(T, 'demand_delta must be an exact integer', [('p', 0, '0')])
    err(V, 'demand_delta must be -100 to 100', [('p', 0, 101)])
    err(T, 'product must be an exact string', [('p', 0, 0), (5, 0, 0)])
    err(T, 'price_delta must be an exact integer', [('p', 0, 0), ('p', '0', 0)])
    err(T, 'demand_delta must be an exact integer', [('p', 0, 0), ('p', 0, '0')])


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
