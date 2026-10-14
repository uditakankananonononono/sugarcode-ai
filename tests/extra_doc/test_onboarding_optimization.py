import random
import pytest
from sugarcode.extra_doc.onboarding_optimization import check_steps as cs

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(steps):
    # written from the stated rule: completions must not rise; below half a nonzero previous is steep; over 30
    probs = []
    previous = None
    for i, (_, c, m) in enumerate(steps):
        if previous is not None:
            if c > previous:
                probs.append((i, 'drop_inverted'))
            elif previous and c * 2 < previous:
                probs.append((i, 'drop_steep'))
        if m > 30:
            probs.append((i, 'slow_step'))
        previous = c
    return {'problems': sorted(probs), 'steps': sorted({s for s, _, _ in steps}), 'total': len(steps)}


DISCLAIMER = ('NOT_CLAIMED: this checks a supplied step list against two drop bars and one time bar. It does not '
              'say the first experience improves, that half or 30 minutes are the right bars, or that any user '
              'finished onboarding. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.onboarding_optimization as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert cs([]) == {'problems': [], 'steps': [], 'total': 0}
    assert cs([('a', 100, 30)]) == {'problems': [], 'steps': ['a'], 'total': 1}
    assert cs([('a', 0, 0)])['problems'] == []
    assert cs([('a', 100, 31)])['problems'] == [(0, 'slow_step')]
    assert cs([('a', 100, 1440)])['problems'] == [(0, 'slow_step')]
    assert cs([('a', 100, 5), ('b', 100, 5)])['problems'] == []
    assert cs([('a', 100, 5), ('b', 101, 5)])['problems'] == [(1, 'drop_inverted')]
    assert cs([('a', 100, 5), ('b', 50, 5)])['problems'] == []
    assert cs([('a', 100, 5), ('b', 49, 5)])['problems'] == [(1, 'drop_steep')]
    assert cs([('a', 1, 5), ('b', 0, 5)])['problems'] == [(1, 'drop_steep')]
    assert cs([('a', 0, 5), ('b', 0, 5)])['problems'] == []
    assert cs([('a', 0, 5), ('b', 1, 5)])['problems'] == [(1, 'drop_inverted')]
    assert cs([('a', 100, 5), ('b', 49, 40)])['problems'] == [(1, 'drop_steep'), (1, 'slow_step')]
    assert cs([('a', 100000, 5), ('b', 50000, 5)])['problems'] == []
    assert cs([('b', 5, 1), ('a', 5, 1)]) == {'problems': [], 'steps': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4460 + part)
    seen, clean = set(), 0
    for _ in range(60):
        steps = []
        for _ in range(rnd.randint(0, 9)):
            steps.append((rnd.choice(('s1', 's2', 's3')),
                          rnd.choice((0, 1, 49, 50, 100, 100000, rnd.randint(0, 200))),
                          rnd.choice((0, 30, 31, 1440, rnd.randint(0, 60)))))
        r = cs(steps)
        assert r == oracle(steps)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'drop_inverted', 'drop_steep', 'slow_step'} and clean >= 2


def test_limits_accepted():
    steps = [('s%02d' % k, 100000 - k, 10) for k in range(40)]
    r = cs(steps)
    assert r['total'] == 40 and r['problems'] == []
    cs([('a' * 24, 100000, 1440)])
    cs([('a', 0, 0)])


def err(exc, msg, steps):
    with pytest.raises(exc) as e:
        cs(steps)
    assert str(e.value) == msg


SM = 'step must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'steps must be an exact list', bad)
    err(V, 'step count must be at most 40', [('s', 0, 0)] * 41)
    for bad in (None, ['s', 0, 0], 'ab', TupleSub(('s', 0, 0)), 5):
        err(T, 'each step must be an exact tuple', [bad])
    for bad in ((), ('s', 0), ('s', 0, 0, 0)):
        err(V, 'each step must have 3 items', [bad])
    for bad in NS:
        err(T, 'step must be an exact string', [(bad, 0, 0)])
    for bad in BAD:
        err(V, SM, [(bad, 0, 0)])
    for bad in NI:
        err(T, 'completions must be an exact integer', [('s', bad, 0)])
        err(T, 'minutes must be an exact integer', [('s', 0, bad)])
    for bad in (-1, 100001, -100, 10**9):
        err(V, 'completions must be 0 to 100000', [('s', bad, 0)])
    for bad in (-1, 1441, -100, 10**9):
        err(V, 'minutes must be 0 to 1440', [('s', 0, bad)])


def _order(err):
    err(T, 'steps must be an exact list', 'x')
    err(V, 'step count must be at most 40', [None] * 41)
    err(T, 'each step must be an exact tuple', [None, ('s',)])
    err(V, 'each step must have 3 items', [('s',), None])
    err(T, 'step must be an exact string', [(5, -1, -1)])
    err(V, SM, [('A', -1, -1)])
    err(T, 'completions must be an exact integer', [('s', '0', -1)])
    err(V, 'completions must be 0 to 100000', [('s', -1, -1)])
    err(T, 'minutes must be an exact integer', [('s', 0, '0')])
    err(V, 'minutes must be 0 to 1440', [('s', 0, -1)])
    err(T, 'step must be an exact string', [('s', 0, 0), (5, 0, 0)])
    err(T, 'completions must be an exact integer', [('s', 0, 0), ('s', '0', 0)])
    err(T, 'minutes must be an exact integer', [('s', 0, 0), ('s', 0, '0')])


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
