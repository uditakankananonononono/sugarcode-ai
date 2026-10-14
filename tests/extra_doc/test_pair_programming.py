import random
import pytest
from sugarcode.extra_doc.pair_programming import check_pairing as cp

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(turns):
    probs = []
    drive = {}
    for i, (s, e, d, n) in enumerate(turns):
        if i == 0 and s != 0:
            probs.append((0, 'late_start'))
        if e - s < 1:
            probs.append((i, 'empty_turn'))
        else:
            drive[d] = drive.get(d, 0) + (e - s)
        if e - s > 30:
            probs.append((i, 'too_long'))
        if d == n:
            probs.append((i, 'same_person'))
        if i > 0:
            ps, pe, pd, pn = turns[i - 1]
            if s != pe:
                probs.append((i, 'gap_or_overlap'))
            if d != pn:
                probs.append((i, 'no_swap'))
    return {'problems': sorted(probs), 'driving': {k: drive[k] for k in sorted(drive)},
            'total': turns[-1][1] if len(turns) else 0}


def test_hand_cases():
    good = [(0, 25, 'a', 'b'), (25, 40, 'b', 'a'), (40, 70, 'a', 'b')]
    assert cp(good) == {'problems': [], 'driving': {'a': 55, 'b': 15}, 'total': 70}
    assert cp([]) == {'problems': [], 'driving': {}, 'total': 0}
    assert cp([(5, 10, 'a', 'b')])['problems'] == [(0, 'late_start')]
    assert cp([(0, 0, 'a', 'b')]) == {'problems': [(0, 'empty_turn')], 'driving': {}, 'total': 0}
    assert cp([(0, 31, 'a', 'b')])['problems'] == [(0, 'too_long')]
    assert cp([(0, 30, 'a', 'b')])['problems'] == []
    assert cp([(0, 10, 'a', 'a')])['problems'] == [(0, 'same_person')]
    assert cp([(0, 10, 'a', 'b'), (11, 20, 'b', 'a')])['problems'] == [(1, 'gap_or_overlap')]
    assert cp([(0, 10, 'a', 'b'), (9, 20, 'b', 'a')])['problems'] == [(1, 'gap_or_overlap')]
    assert cp([(0, 10, 'a', 'b'), (10, 20, 'a', 'b')])['problems'] == [(1, 'no_swap')]
    assert cp([(0, 10, 'a', 'b'), (10, 20, 'c', 'a')])['problems'] == [(1, 'no_swap')]    # driver must be the old navigator
    assert cp([(0, 10, 'a', 'b'), (10, 5, 'b', 'a')]) == {
        'problems': [(1, 'empty_turn')], 'driving': {'a': 10}, 'total': 5}                    # a backwards turn adds no minutes
    assert cp([(5, 5, 'a', 'a')])['problems'] == [(0, 'empty_turn'), (0, 'late_start'), (0, 'same_person')]


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(6910 + part)
    seen, clean = set(), 0
    for _ in range(60):
        if rnd.random() < 0.5:
            t, turns, who = 0, [], ['a', 'b']
            for _ in range(rnd.randint(1, 5)):
                ln = rnd.randint(1, 30)
                turns.append((t, t + ln, who[0], who[1]))
                t += ln
                who.reverse()
            if rnd.random() < 0.4:
                i = rnd.randrange(len(turns))
                turns[i] = (rnd.randint(0, 40), rnd.randint(0, 80), rnd.choice('ab'), rnd.choice('ab'))
        else:
            turns = [(rnd.randint(0, 40), rnd.randint(0, 80), rnd.choice('ab'), rnd.choice('ab')) for _ in range(rnd.randint(0, 5))]
        r = cp(turns)
        assert r == oracle(turns)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert len(seen) == 6 and clean > 5


def test_limits_accepted():
    turns = []
    t = 0
    for i in range(40):
        turns.append((t, t + 15, 'a' if i % 2 == 0 else 'b', 'b' if i % 2 == 0 else 'a'))
        t += 15
    assert t == 600 and cp(turns) == {'problems': [], 'driving': {'a': 300, 'b': 300}, 'total': 600}
    cp([(0, 600, 'a' * 24, 'b' * 24)])


def err(exc, msg, turns):
    with pytest.raises(exc) as e:
        cp(turns)
    assert str(e.value) == msg


NM = 'name must be 1 to 24 lowercase identifier characters'
MR = 'minute must be between 0 and 600'
MT = 'minute must be an exact int'
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')
NS = (None, 5, b'a', StrSub('a'))


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'turns must be an exact list', bad)
    err(V, 'turn count must be at most 40', [(0, 1, 'a', 'b')] * 41)
    for bad in (None, [0, 1, 'a', 'b'], 'abcd', TupleSub((0, 1, 'a', 'b')), 5):
        err(T, 'each turn must be an exact tuple', [bad])
    for bad in ((), (0, 1, 'a'), (0, 1, 'a', 'b', 1)):
        err(V, 'each turn must have 4 items', [bad])
    for bad in (None, 1.0, '1', True, False, IntSub(1), b'1'):
        err(T, MT, [(bad, 1, 'a', 'b')])
        err(T, MT, [(0, bad, 'a', 'b')])
    for bad in (-1, 601, 2 ** 40):
        err(V, MR, [(bad, 1, 'a', 'b')])
        err(V, MR, [(0, bad, 'a', 'b')])
    for bad in NS:
        err(T, 'name must be an exact string', [(0, 1, bad, 'b')])
        err(T, 'name must be an exact string', [(0, 1, 'a', bad)])
    for bad in BAD:
        err(V, NM, [(0, 1, bad, 'b')])
        err(V, NM, [(0, 1, 'a', bad)])


def _order(err):
    err(T, 'turns must be an exact list', 'x')
    err(V, 'turn count must be at most 40', [None] * 41)
    err(T, 'each turn must be an exact tuple', [None, ('a',)])
    err(V, 'each turn must have 4 items', [('a',), None])
    err(T, MT, [('x', 2 ** 40, 5, 5)])
    err(V, MR, [(2 ** 40, 'x', 5, 5)])
    err(T, MT, [(0, 'x', 5, 5)])
    err(T, 'name must be an exact string', [(0, 1, 5, 'A')])
    err(V, NM, [(0, 1, 'A', 5)])
    err(T, 'name must be an exact string', [(0, 1, 'a', 5)])
    err(T, MT, [(0, 1, 'a', 'b'), ('x', 0, 5, 5)])
    err(T, 'name must be an exact string', [(0, 1, 5, 'b'), ('x', 0, 5, 5)])

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
