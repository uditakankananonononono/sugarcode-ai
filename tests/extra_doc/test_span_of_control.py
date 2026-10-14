import random
import pytest
from sugarcode.extra_doc.span_of_control import check_teams as ct

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
    # written from the stated rule: over 10 reports is overloaded; under 3 is narrow
    probs = []
    for i, (_, r) in enumerate(teams):
        if r > 10:
            probs.append((i, 'overloaded'))
        if r < 3:
            probs.append((i, 'narrow'))
    return {'problems': sorted(probs), 'managers': sorted({m for m, _ in teams}), 'total': len(teams)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied report counts against two ratio bars. It does not say the '
              'management ratio is right, that 3 or 10 are the right bars, or that any team is well run. '
              'No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.span_of_control as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ct([]) == {'problems': [], 'managers': [], 'total': 0}
    assert ct([('a', 3)]) == {'problems': [], 'managers': ['a'], 'total': 1}
    assert ct([('a', 10)])['problems'] == []
    assert ct([('a', 11)])['problems'] == [(0, 'overloaded')]
    assert ct([('a', 100)])['problems'] == [(0, 'overloaded')]
    assert ct([('a', 2)])['problems'] == [(0, 'narrow')]
    assert ct([('a', 0)])['problems'] == [(0, 'narrow')]
    assert ct([('a', 11), ('b', 5), ('c', 0)])['problems'] == [(0, 'overloaded'), (2, 'narrow')]
    assert ct([('b', 5), ('a', 5)]) == {'problems': [], 'managers': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4790 + part)
    seen, clean = set(), 0
    for _ in range(60):
        teams = []
        for _ in range(rnd.randint(0, 9)):
            teams.append((rnd.choice(('m1', 'm2', 'm3')),
                          rnd.choice((0, 2, 3, 10, 11, 100, rnd.randint(0, 100)))))
        r = ct(teams)
        assert r == oracle(teams)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'overloaded', 'narrow'} and clean >= 2


def test_limits_accepted():
    teams = [('m%02d' % k, 5) for k in range(40)]
    r = ct(teams)
    assert r['total'] == 40 and r['problems'] == []
    ct([('a' * 24, 100)])
    ct([('a', 0)])


def err(exc, msg, teams):
    with pytest.raises(exc) as e:
        ct(teams)
    assert str(e.value) == msg


MM = 'manager must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'teams must be an exact list', bad)
    err(V, 'team count must be at most 40', [('m', 5)] * 41)
    for bad in (None, ['m', 5], 'ab', TupleSub(('m', 5)), 5):
        err(T, 'each team must be an exact tuple', [bad])
    for bad in ((), ('m',), ('m', 5, 0)):
        err(V, 'each team must have 2 items', [bad])
    for bad in NS:
        err(T, 'manager must be an exact string', [(bad, 5)])
    for bad in BAD:
        err(V, MM, [(bad, 5)])
    for bad in NI:
        err(T, 'reports must be an exact integer', [('m', bad)])
    for bad in (-1, 101, -100, 10**9):
        err(V, 'reports must be 0 to 100', [('m', bad)])


def _order(err):
    err(T, 'teams must be an exact list', 'x')
    err(V, 'team count must be at most 40', [None] * 41)
    err(T, 'each team must be an exact tuple', [None, ('m',)])
    err(V, 'each team must have 2 items', [('m',), None])
    err(T, 'manager must be an exact string', [(5, -1)])
    err(V, MM, [('A', -1)])
    err(T, 'reports must be an exact integer', [('m', '0')])
    err(V, 'reports must be 0 to 100', [('m', -1)])
    err(T, 'manager must be an exact string', [('m', 5), (5, 5)])
    err(T, 'reports must be an exact integer', [('m', 5), ('m', '0')])


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
