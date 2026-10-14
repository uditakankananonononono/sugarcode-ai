import random
import pytest
from sugarcode.extra_doc.revenue_model_design import check_streams as cs

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(streams):
    # written from the stated rule: share over 50 is dominant; share at least 20 with negative margin is bleeding
    probs = []
    for i, (_, sh, m) in enumerate(streams):
        if sh > 50:
            probs.append((i, 'dominant'))
        if sh >= 20 and m < 0:
            probs.append((i, 'bleeding'))
    return {'problems': sorted(probs), 'streams': sorted({x for x, _, _ in streams}), 'total': len(streams)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied stream shares against two mix bars. It does not say the revenue '
              'model is structured well, that 50 or 20 percent are the right bars, or that any revenue arrived. '
              'No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.revenue_model_design as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert cs([]) == {'problems': [], 'streams': [], 'total': 0}
    assert cs([('s', 50, 5)]) == {'problems': [], 'streams': ['s'], 'total': 1}
    assert cs([('s', 50, -5)])['problems'] == [(0, 'bleeding')]
    assert cs([('s', 51, 0)])['problems'] == [(0, 'dominant')]
    assert cs([('s', 100, 0)])['problems'] == [(0, 'dominant')]
    assert cs([('s', 20, -1)])['problems'] == [(0, 'bleeding')]
    assert cs([('s', 20, 0)])['problems'] == []
    assert cs([('s', 19, -100)])['problems'] == []
    assert cs([('s', 1, -100)])['problems'] == []
    assert cs([('s', 100, -1)])['problems'] == [(0, 'bleeding'), (0, 'dominant')]
    assert cs([('s', 51, -1)])['problems'] == [(0, 'bleeding'), (0, 'dominant')]
    assert cs([('a', 60, 1), ('b', 25, -2), ('c', 10, -9)])['problems'] == [(0, 'dominant'), (1, 'bleeding')]
    assert cs([('b', 10, 1), ('a', 10, 1)]) == {'problems': [], 'streams': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4360 + part)
    seen, clean = set(), 0
    for _ in range(60):
        streams = []
        for _ in range(rnd.randint(0, 9)):
            streams.append((rnd.choice(('s1', 's2', 's3')),
                            rnd.choice((1, 19, 20, 50, 51, 100, rnd.randint(1, 100))),
                            rnd.choice((-100, -1, 0, 1, 100, rnd.randint(-100, 100)))))
        r = cs(streams)
        assert r == oracle(streams)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'dominant', 'bleeding'} and clean >= 2


def test_limits_accepted():
    streams = [('s%02d' % k, 2, 5) for k in range(40)]
    r = cs(streams)
    assert r['total'] == 40 and r['problems'] == []
    cs([('a' * 24, 100, 100)])
    cs([('a', 1, -100)])


def err(exc, msg, streams):
    with pytest.raises(exc) as e:
        cs(streams)
    assert str(e.value) == msg


SM = 'stream must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'streams must be an exact list', bad)
    err(V, 'stream count must be at most 40', [('s', 1, 0)] * 41)
    for bad in (None, ['s', 1, 0], 'ab', TupleSub(('s', 1, 0)), 5):
        err(T, 'each stream must be an exact tuple', [bad])
    for bad in ((), ('s', 1), ('s', 1, 0, 0)):
        err(V, 'each stream must have 3 items', [bad])
    for bad in NS:
        err(T, 'stream must be an exact string', [(bad, 1, 0)])
    for bad in BAD:
        err(V, SM, [(bad, 1, 0)])
    for bad in NI:
        err(T, 'share must be an exact integer', [('s', bad, 0)])
        err(T, 'margin must be an exact integer', [('s', 1, bad)])
    for bad in (0, 101, -1, 10**9):
        err(V, 'share must be 1 to 100', [('s', bad, 0)])
    for bad in (-101, 101, -1000, 10**9):
        err(V, 'margin must be -100 to 100', [('s', 1, bad)])


def _order(err):
    err(T, 'streams must be an exact list', 'x')
    err(V, 'stream count must be at most 40', [None] * 41)
    err(T, 'each stream must be an exact tuple', [None, ('s',)])
    err(V, 'each stream must have 3 items', [('s',), None])
    err(T, 'stream must be an exact string', [(5, 1, 0)])
    err(V, SM, [('A', 1, 0)])
    err(T, 'share must be an exact integer', [('s', '1', 0)])
    err(V, 'share must be 1 to 100', [('s', 0, 0)])
    err(T, 'margin must be an exact integer', [('s', 1, '0')])
    err(V, 'margin must be -100 to 100', [('s', 1, 101)])
    err(T, 'stream must be an exact string', [('s', 1, 0), (5, 1, 0)])
    err(T, 'share must be an exact integer', [('s', 1, 0), ('s', '1', 0)])
    err(T, 'margin must be an exact integer', [('s', 1, 0), ('s', 1, '0')])


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
