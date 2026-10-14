import random
import pytest
from sugarcode.extra_doc.kpi_selection import check_metrics as ck

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(metrics):
    # written from the stated rule: under 1 data source is unsourced; under 2 reviews is drifting
    probs = []
    for i, (_, a, b) in enumerate(metrics):
        if a < 1:
            probs.append((i, 'unsourced'))
        if b < 2:
            probs.append((i, 'drifting'))
    return {'problems': sorted(probs), 'metrics': sorted({x for x, _, _ in metrics}), 'total': len(metrics)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied metric numbers against two choice bars. It does not say the '
              'right metrics were chosen, that 1 source or 2 reviews are the right bars, or that any number '
              'moves. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.kpi_selection as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'metrics': [], 'total': 0}
    assert ck([('a', 1, 2)]) == {'problems': [], 'metrics': ['a'], 'total': 1}
    assert ck([('a', 0, 2)])['problems'] == [(0, 'unsourced')]
    assert ck([('a', 10, 2)])['problems'] == []
    assert ck([('a', 1, 1)])['problems'] == [(0, 'drifting')]
    assert ck([('a', 1, 0)])['problems'] == [(0, 'drifting')]
    assert ck([('a', 0, 1)])['problems'] == [(0, 'drifting'), (0, 'unsourced')]
    assert ck([('a', 0, 1), ('b', 3, 4), ('c', 10, 12)])['problems'] == [(0, 'drifting'), (0, 'unsourced')]
    assert ck([('b', 3, 4), ('a', 3, 4)]) == {'problems': [], 'metrics': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4920 + part)
    seen, clean = set(), 0
    for _ in range(60):
        metrics = []
        for _ in range(rnd.randint(0, 9)):
            metrics.append((rnd.choice(('x1', 'x2', 'x3')),
                            rnd.choice((0, 1, 10, rnd.randint(0, 10))),
                            rnd.choice((0, 1, 2, 12, rnd.randint(0, 12)))))
        r = ck(metrics)
        assert r == oracle(metrics)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'unsourced', 'drifting'} and clean >= 2


def test_limits_accepted():
    metrics = [('x%02d' % k, 3, 4) for k in range(40)]
    r = ck(metrics)
    assert r['total'] == 40 and r['problems'] == []
    ck([('a' * 24, 10, 12)])
    ck([('a', 0, 0)])


def err(exc, msg, metrics):
    with pytest.raises(exc) as e:
        ck(metrics)
    assert str(e.value) == msg


NM = 'metric must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'metrics must be an exact list', bad)
    err(V, 'metric count must be at most 40', [('x', 3, 4)] * 41)
    for bad in (None, ['x', 3, 4], 'ab', TupleSub(('x', 3, 4)), 5):
        err(T, 'each metric must be an exact tuple', [bad])
    for bad in ((), ('x', 3), ('x', 3, 4, 0)):
        err(V, 'each metric must have 3 items', [bad])
    for bad in NS:
        err(T, 'metric must be an exact string', [(bad, 3, 4)])
    for bad in BAD:
        err(V, NM, [(bad, 3, 4)])
    for bad in NI:
        err(T, 'sources must be an exact integer', [('x', bad, 4)])
        err(T, 'reviews must be an exact integer', [('x', 3, bad)])
    for bad in (-1, 11, -100, 10**9):
        err(V, 'sources must be 0 to 10', [('x', bad, 4)])
    for bad in (-1, 13, -100, 10**9):
        err(V, 'reviews must be 0 to 12', [('x', 3, bad)])


def _order(err):
    err(T, 'metrics must be an exact list', 'x')
    err(V, 'metric count must be at most 40', [None] * 41)
    err(T, 'each metric must be an exact tuple', [None, ('x',)])
    err(V, 'each metric must have 3 items', [('x',), None])
    err(T, 'metric must be an exact string', [(5, -1, -1)])
    err(V, NM, [('A', -1, -1)])
    err(T, 'sources must be an exact integer', [('x', '0', -1)])
    err(V, 'sources must be 0 to 10', [('x', -1, -1)])
    err(T, 'reviews must be an exact integer', [('x', 0, '0')])
    err(V, 'reviews must be 0 to 12', [('x', 0, -1)])
    err(T, 'metric must be an exact string', [('x', 3, 4), (5, 3, 4)])
    err(T, 'sources must be an exact integer', [('x', 3, 4), ('x', '0', 4)])
    err(T, 'reviews must be an exact integer', [('x', 3, 4), ('x', 3, '0')])


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
