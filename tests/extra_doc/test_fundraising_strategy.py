import random
import pytest
from sugarcode.extra_doc.fundraising_strategy import check_rounds as ck

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(rounds):
    # written from the stated rule: under 100 thousand sought is too small; over 18 months is slow
    probs = []
    for i, (_, a, b) in enumerate(rounds):
        if a < 100:
            probs.append((i, 'too_small'))
        if b > 18:
            probs.append((i, 'slow_raise'))
    return {'problems': sorted(probs), 'rounds': sorted({x for x, _, _ in rounds}), 'total': len(rounds)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied round numbers against two capital bars. It does not say capital '
              'is raised, that 100 thousand or 18 months are the right bars, or that any investor commits. '
              'No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.fundraising_strategy as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'rounds': [], 'total': 0}
    assert ck([('a', 100, 18)]) == {'problems': [], 'rounds': ['a'], 'total': 1}
    assert ck([('a', 99, 18)])['problems'] == [(0, 'too_small')]
    assert ck([('a', 0, 18)])['problems'] == [(0, 'too_small')]
    assert ck([('a', 100000, 18)])['problems'] == []
    assert ck([('a', 100, 19)])['problems'] == [(0, 'slow_raise')]
    assert ck([('a', 100, 36)])['problems'] == [(0, 'slow_raise')]
    assert ck([('a', 99, 19)])['problems'] == [(0, 'slow_raise'), (0, 'too_small')]
    assert ck([('a', 99, 19), ('b', 500, 12), ('c', 100000, 36)])['problems'] == [
        (0, 'slow_raise'), (0, 'too_small'), (2, 'slow_raise')]
    assert ck([('b', 500, 12), ('a', 500, 12)]) == {'problems': [], 'rounds': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4980 + part)
    seen, clean = set(), 0
    for _ in range(60):
        rounds = []
        for _ in range(rnd.randint(0, 9)):
            rounds.append((rnd.choice(('x1', 'x2', 'x3')),
                           rnd.choice((0, 99, 100, 100000, rnd.randint(0, 100000))),
                           rnd.choice((0, 18, 19, 36, rnd.randint(0, 36)))))
        r = ck(rounds)
        assert r == oracle(rounds)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'too_small', 'slow_raise'} and clean >= 2


def test_limits_accepted():
    rounds = [('x%02d' % k, 500, 12) for k in range(40)]
    r = ck(rounds)
    assert r['total'] == 40 and r['problems'] == []
    ck([('a' * 24, 100000, 36)])
    ck([('a', 0, 0)])


def err(exc, msg, rounds):
    with pytest.raises(exc) as e:
        ck(rounds)
    assert str(e.value) == msg


NM = 'round must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'rounds must be an exact list', bad)
    err(V, 'round count must be at most 40', [('x', 500, 12)] * 41)
    for bad in (None, ['x', 500, 12], 'ab', TupleSub(('x', 500, 12)), 5):
        err(T, 'each round must be an exact tuple', [bad])
    for bad in ((), ('x', 500), ('x', 500, 12, 0)):
        err(V, 'each round must have 3 items', [bad])
    for bad in NS:
        err(T, 'round must be an exact string', [(bad, 500, 12)])
    for bad in BAD:
        err(V, NM, [(bad, 500, 12)])
    for bad in NI:
        err(T, 'target_k must be an exact integer', [('x', bad, 12)])
        err(T, 'months must be an exact integer', [('x', 500, bad)])
    for bad in (-1, 100001, -100, 10**9):
        err(V, 'target_k must be 0 to 100000', [('x', bad, 12)])
    for bad in (-1, 37, -100, 10**9):
        err(V, 'months must be 0 to 36', [('x', 500, bad)])


def _order(err):
    err(T, 'rounds must be an exact list', 'x')
    err(V, 'round count must be at most 40', [None] * 41)
    err(T, 'each round must be an exact tuple', [None, ('x',)])
    err(V, 'each round must have 3 items', [('x',), None])
    err(T, 'round must be an exact string', [(5, -1, -1)])
    err(V, NM, [('A', -1, -1)])
    err(T, 'target_k must be an exact integer', [('x', '0', -1)])
    err(V, 'target_k must be 0 to 100000', [('x', -1, -1)])
    err(T, 'months must be an exact integer', [('x', 0, '0')])
    err(V, 'months must be 0 to 36', [('x', 0, -1)])
    err(T, 'round must be an exact string', [('x', 500, 12), (5, 500, 12)])
    err(T, 'target_k must be an exact integer', [('x', 500, 12), ('x', '0', 12)])
    err(T, 'months must be an exact integer', [('x', 500, 12), ('x', 500, '0')])


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
