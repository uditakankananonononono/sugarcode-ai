import random
import pytest
from sugarcode.extra_doc.team_topology_design import check_flow as cf

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(teams):
    # written from the stated rule: over 9 members is oversized; over 2 dependencies is tangled
    probs = []
    for i, (_, s, d) in enumerate(teams):
        if s > 9:
            probs.append((i, 'oversized'))
        if d > 2:
            probs.append((i, 'tangled'))
    return {'problems': sorted(probs), 'teams': sorted({t for t, _, _ in teams}), 'total': len(teams)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied team numbers against two flow bars. It does not say the '
              'structure flows, that 9 members or 2 dependencies are the right bars, or that any team ships. '
              'No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.team_topology_design as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert cf([]) == {'problems': [], 'teams': [], 'total': 0}
    assert cf([('a', 9, 2)]) == {'problems': [], 'teams': ['a'], 'total': 1}
    assert cf([('a', 10, 2)])['problems'] == [(0, 'oversized')]
    assert cf([('a', 20, 0)])['problems'] == [(0, 'oversized')]
    assert cf([('a', 9, 3)])['problems'] == [(0, 'tangled')]
    assert cf([('a', 0, 10)])['problems'] == [(0, 'tangled')]
    assert cf([('a', 0, 0)])['problems'] == []
    assert cf([('a', 10, 3)])['problems'] == [(0, 'oversized'), (0, 'tangled')]
    assert cf([('a', 10, 3), ('b', 5, 1), ('c', 20, 10)])['problems'] == [
        (0, 'oversized'), (0, 'tangled'), (2, 'oversized'), (2, 'tangled')]
    assert cf([('b', 5, 1), ('a', 5, 1)]) == {'problems': [], 'teams': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4810 + part)
    seen, clean = set(), 0
    for _ in range(60):
        teams = []
        for _ in range(rnd.randint(0, 9)):
            teams.append((rnd.choice(('t1', 't2', 't3')),
                          rnd.choice((0, 9, 10, 20, rnd.randint(0, 20))),
                          rnd.choice((0, 2, 3, 10, rnd.randint(0, 10)))))
        r = cf(teams)
        assert r == oracle(teams)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'oversized', 'tangled'} and clean >= 2


def test_limits_accepted():
    teams = [('t%02d' % k, 9, 2) for k in range(40)]
    r = cf(teams)
    assert r['total'] == 40 and r['problems'] == []
    cf([('a' * 24, 20, 10)])
    cf([('a', 0, 0)])


def err(exc, msg, teams):
    with pytest.raises(exc) as e:
        cf(teams)
    assert str(e.value) == msg


TM = 'team must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'teams must be an exact list', bad)
    err(V, 'team count must be at most 40', [('t', 5, 1)] * 41)
    for bad in (None, ['t', 5, 1], 'ab', TupleSub(('t', 5, 1)), 5):
        err(T, 'each team must be an exact tuple', [bad])
    for bad in ((), ('t', 5), ('t', 5, 1, 0)):
        err(V, 'each team must have 3 items', [bad])
    for bad in NS:
        err(T, 'team must be an exact string', [(bad, 5, 1)])
    for bad in BAD:
        err(V, TM, [(bad, 5, 1)])
    for bad in NI:
        err(T, 'size must be an exact integer', [('t', bad, 1)])
        err(T, 'dependencies must be an exact integer', [('t', 5, bad)])
    for bad in (-1, 21, -100, 10**9):
        err(V, 'size must be 0 to 20', [('t', bad, 1)])
    for bad in (-1, 11, -100, 10**9):
        err(V, 'dependencies must be 0 to 10', [('t', 5, bad)])


def _order(err):
    err(T, 'teams must be an exact list', 'x')
    err(V, 'team count must be at most 40', [None] * 41)
    err(T, 'each team must be an exact tuple', [None, ('t',)])
    err(V, 'each team must have 3 items', [('t',), None])
    err(T, 'team must be an exact string', [(5, -1, -1)])
    err(V, TM, [('A', -1, -1)])
    err(T, 'size must be an exact integer', [('t', '0', -1)])
    err(V, 'size must be 0 to 20', [('t', -1, -1)])
    err(T, 'dependencies must be an exact integer', [('t', 0, '0')])
    err(V, 'dependencies must be 0 to 10', [('t', 0, -1)])
    err(T, 'team must be an exact string', [('t', 5, 1), (5, 5, 1)])
    err(T, 'size must be an exact integer', [('t', 5, 1), ('t', '0', 1)])
    err(T, 'dependencies must be an exact integer', [('t', 5, 1), ('t', 5, '0')])


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
