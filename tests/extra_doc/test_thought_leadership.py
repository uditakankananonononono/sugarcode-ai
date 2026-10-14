import random
import pytest
from sugarcode.extra_doc.thought_leadership import check_pieces as cp

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


PUFFERY = ('world-class', 'best-in-class')


def oracle(pieces):
    # written from the stated rule: no claims; any claim without a digit; folded claim holding a puffery phrase
    probs = [(i, 'no_evidence') for i, (_, cs) in enumerate(pieces) if len(cs) == 0]
    probs += [(i, 'unfounded') for i, (_, cs) in enumerate(pieces)
              if any(not [ch for ch in c if '0' <= ch <= '9'] for c in cs)]
    probs += [(i, 'puffery') for i, (_, cs) in enumerate(pieces)
              if any(p in ' '.join(c.lower().split()) for c in cs for p in PUFFERY)]
    probs += [(i, 'repeat') for i in range(len(pieces)) if pieces[i][0] in [p[0] for p in pieces[:i]]]
    return {'problems': sorted(probs), 'claims': sum(len(cs) for _, cs in pieces), 'total': len(pieces)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied text for digits and two fixed phrases. It does not say the claims '
              'are true, that numbers prove expertise, or that anyone was persuaded. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.thought_leadership as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert cp([]) == {'problems': [], 'claims': 0, 'total': 0}
    assert cp([('T', ['we shipped 40 features'])]) == {'problems': [], 'claims': 1, 'total': 1}
    assert cp([('T', [])])['problems'] == [(0, 'no_evidence')]
    assert cp([('T', ['we ship fast'])])['problems'] == [(0, 'unfounded')]
    assert cp([('T', ['we ship fast', '40 teams'])])['problems'] == [(0, 'unfounded')]   # once per piece
    assert cp([('T', ['a world-class team of 9'])])['problems'] == [(0, 'puffery')]
    assert cp([('T', ['World-Class  results in 9 days'])])['problems'] == [(0, 'puffery')]
    assert cp([('T', ['best-in-class support'])])['problems'] == [(0, 'puffery'), (0, 'unfounded')]
    assert cp([('T', ['world class results 9'])])['problems'] == []                     # no hyphen, no match
    assert cp([('A', ['1']), ('A', ['2'])])['problems'] == [(1, 'repeat')]
    assert cp([('T', ['９ digits are ASCII-only here'])])['problems'] == [(0, 'unfounded')]  # fullwidth ９ is not 0-9
    assert cp([('T', ['café v2'])])['problems'] == []


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4150 + part)
    seen, clean = set(), 0
    bag = ['we ship fast', '40 teams switched', 'world-class crew', 'Best-In-Class 9x', 'café v2',
           'no digits here', '９ fullwidth', 'plain 2', 'best-in-class support']
    for _ in range(60):
        pieces = []
        for _ in range(rnd.randint(0, 6)):
            pieces.append((rnd.choice(('T1', 'T2', 'T3')), [rnd.choice(bag) for _ in range(rnd.randint(0, 3))]))
        r = cp(pieces)
        assert r == oracle(pieces)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert len(seen) == 4 and clean >= 2


def test_limits_accepted():
    pieces = [('t%02d' % k, ['claim %d' % k] * 5) for k in range(20)]
    r = cp(pieces)
    assert r['problems'] == [] and r['claims'] == 100 and r['total'] == 20
    cp([('x' * 100, ['y' * 120])])


def err(exc, msg, pieces):
    with pytest.raises(exc) as e:
        cp(pieces)
    assert str(e.value) == msg


TL = 'title length must be 1 to 100 characters'
CM = 'claim length must be 1 to 120 characters'
NS = (None, 5, b'a', StrSub('a'))


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'pieces must be an exact list', bad)
    err(V, 'piece count must be at most 20', [('t', [])] * 21)
    for bad in (None, ['t', []], 'ab', TupleSub(('t', [])), 5):
        err(T, 'each piece must be an exact tuple', [bad])
    for bad in ((), ('t',), ('t', [], 1)):
        err(V, 'each piece must have 2 items', [bad])
    for bad in NS:
        err(T, 'title must be an exact string', [(bad, [])])
    for bad in ('', 'x' * 101):
        err(V, TL, [(bad, [])])
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'claims must be an exact list', [('t', bad)])
    err(V, 'claim count must be at most 5', [('t', ['c'] * 6)])
    for bad in NS:
        err(T, 'each claim must be an exact string', [('t', [bad])])
    for bad in ('', 'x' * 121):
        err(V, CM, [('t', [bad])])


def _order(err):
    err(T, 'pieces must be an exact list', 'x')
    err(V, 'piece count must be at most 20', [None] * 21)
    err(T, 'each piece must be an exact tuple', [None, ('t',)])
    err(V, 'each piece must have 2 items', [('t',), None])
    err(T, 'title must be an exact string', [(5, 'x')])
    err(V, TL, [('', 5)])
    err(T, 'claims must be an exact list', [('t', 5)])
    err(V, 'claim count must be at most 5', [('t', ['c'] * 6), (5, 'x')])
    err(T, 'each claim must be an exact string', [('t', [5, ''])])
    err(V, CM, [('t', ['', 5])])
    err(T, 'title must be an exact string', [('t', []), (5, 'x')])
    err(T, 'claims must be an exact list', [('t', []), ('t', 5)])


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
