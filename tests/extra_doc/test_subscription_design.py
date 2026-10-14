import random
import pytest
from sugarcode.extra_doc.subscription_design import check_tiers as ct

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(tiers):
    # written from the stated rule: each tier must top the previous; over ten times a nonzero previous is wide
    probs = []
    previous = None
    for i, (_, c) in enumerate(tiers):
        if previous is not None:
            if c <= previous:
                probs.append((i, 'not_dearer'))
            elif previous > 0 and c > 10 * previous:
                probs.append((i, 'gap_wide'))
        previous = c
    return {'problems': sorted(probs), 'tiers': sorted({t for t, _ in tiers}), 'total': len(tiers)}


DISCLAIMER = ('NOT_CLAIMED: this checks a supplied ladder against two spacing bars. It does not say the tiers '
              'create recurring revenue, that ten times is the right gap, or that anyone subscribed. No '
              'clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.subscription_design as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ct([]) == {'problems': [], 'tiers': [], 'total': 0}
    assert ct([('a', 0)]) == {'problems': [], 'tiers': ['a'], 'total': 1}
    assert ct([('a', 1000000)])['problems'] == []
    assert ct([('a', 100), ('b', 100)])['problems'] == [(1, 'not_dearer')]
    assert ct([('a', 100), ('b', 99)])['problems'] == [(1, 'not_dearer')]
    assert ct([('a', 100), ('b', 101)])['problems'] == []
    assert ct([('a', 100), ('b', 1000)])['problems'] == []
    assert ct([('a', 100), ('b', 1001)])['problems'] == [(1, 'gap_wide')]
    assert ct([('a', 1), ('b', 11)])['problems'] == [(1, 'gap_wide')]
    assert ct([('a', 1), ('b', 10)])['problems'] == []
    assert ct([('a', 0), ('b', 1000000)])['problems'] == []
    assert ct([('a', 0), ('b', 0)])['problems'] == [(1, 'not_dearer')]
    assert ct([('a', 10), ('b', 5), ('c', 500)])['problems'] == [(1, 'not_dearer'), (2, 'gap_wide')]
    assert ct([('b', 1), ('a', 2)]) == {'problems': [], 'tiers': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4370 + part)
    seen, clean = set(), 0
    for _ in range(60):
        tiers = []
        for _ in range(rnd.randint(0, 9)):
            tiers.append((rnd.choice(('t1', 't2', 't3')),
                          rnd.choice((0, 1, 10, 11, 100, 1000, 1001, 1000000, rnd.randint(0, 2000)))))
        r = ct(tiers)
        assert r == oracle(tiers)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'not_dearer', 'gap_wide'} and clean >= 2


def test_limits_accepted():
    tiers = [('t%02d' % k, k + 1) for k in range(40)]
    r = ct(tiers)
    assert r['total'] == 40 and r['problems'] == []
    ct([('a' * 24, 1000000)])
    ct([('a', 0)])


def err(exc, msg, tiers):
    with pytest.raises(exc) as e:
        ct(tiers)
    assert str(e.value) == msg


TM = 'tier must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'tiers must be an exact list', bad)
    err(V, 'tier count must be at most 40', [('t', 0)] * 41)
    for bad in (None, ['t', 0], 'ab', TupleSub(('t', 0)), 5):
        err(T, 'each tier must be an exact tuple', [bad])
    for bad in ((), ('t',), ('t', 0, 0)):
        err(V, 'each tier must have 2 items', [bad])
    for bad in NS:
        err(T, 'tier must be an exact string', [(bad, 0)])
    for bad in BAD:
        err(V, TM, [(bad, 0)])
    for bad in NI:
        err(T, 'monthly_cents must be an exact integer', [('t', bad)])
    for bad in (-1, 1000001, -100, 10**9):
        err(V, 'monthly_cents must be 0 to 1000000', [('t', bad)])


def _order(err):
    err(T, 'tiers must be an exact list', 'x')
    err(V, 'tier count must be at most 40', [None] * 41)
    err(T, 'each tier must be an exact tuple', [None, ('t',)])
    err(V, 'each tier must have 2 items', [('t',), None])
    err(T, 'tier must be an exact string', [(5, -1)])
    err(V, TM, [('A', -1)])
    err(T, 'monthly_cents must be an exact integer', [('t', '0')])
    err(V, 'monthly_cents must be 0 to 1000000', [('t', -1)])
    err(T, 'tier must be an exact string', [('t', 0), (5, 0)])
    err(T, 'monthly_cents must be an exact integer', [('t', 0), ('t', '0')])


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
