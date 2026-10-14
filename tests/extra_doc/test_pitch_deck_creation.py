import random
import pytest
from sugarcode.extra_doc.pitch_deck_creation import check_decks as ck

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(decks):
    # written from the stated rule: under 10 slides is thin; over 20 minutes is overlong
    probs = []
    for i, (_, a, b) in enumerate(decks):
        if a < 10:
            probs.append((i, 'thin_deck'))
        if b > 20:
            probs.append((i, 'overlong'))
    return {'problems': sorted(probs), 'decks': sorted({x for x, _, _ in decks}), 'total': len(decks)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied deck numbers against two presentation bars. It does not say '
              'the presentation persuades, that 10 slides or 20 minutes are the right bars, or that any '
              'investor signs. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.pitch_deck_creation as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'decks': [], 'total': 0}
    assert ck([('a', 10, 20)]) == {'problems': [], 'decks': ['a'], 'total': 1}
    assert ck([('a', 9, 20)])['problems'] == [(0, 'thin_deck')]
    assert ck([('a', 0, 20)])['problems'] == [(0, 'thin_deck')]
    assert ck([('a', 40, 20)])['problems'] == []
    assert ck([('a', 10, 21)])['problems'] == [(0, 'overlong')]
    assert ck([('a', 10, 60)])['problems'] == [(0, 'overlong')]
    assert ck([('a', 9, 21)])['problems'] == [(0, 'overlong'), (0, 'thin_deck')]
    assert ck([('a', 9, 21), ('b', 15, 15), ('c', 40, 60)])['problems'] == [
        (0, 'overlong'), (0, 'thin_deck'), (2, 'overlong')]
    assert ck([('b', 15, 15), ('a', 15, 15)]) == {'problems': [], 'decks': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4990 + part)
    seen, clean = set(), 0
    for _ in range(60):
        decks = []
        for _ in range(rnd.randint(0, 9)):
            decks.append((rnd.choice(('x1', 'x2', 'x3')),
                          rnd.choice((0, 9, 10, 40, rnd.randint(0, 40))),
                          rnd.choice((0, 20, 21, 60, rnd.randint(0, 60)))))
        r = ck(decks)
        assert r == oracle(decks)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'thin_deck', 'overlong'} and clean >= 2


def test_limits_accepted():
    decks = [('x%02d' % k, 15, 15) for k in range(40)]
    r = ck(decks)
    assert r['total'] == 40 and r['problems'] == []
    ck([('a' * 24, 40, 60)])
    ck([('a', 0, 0)])


def err(exc, msg, decks):
    with pytest.raises(exc) as e:
        ck(decks)
    assert str(e.value) == msg


NM = 'deck must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'decks must be an exact list', bad)
    err(V, 'deck count must be at most 40', [('x', 15, 15)] * 41)
    for bad in (None, ['x', 15, 15], 'ab', TupleSub(('x', 15, 15)), 5):
        err(T, 'each deck must be an exact tuple', [bad])
    for bad in ((), ('x', 15), ('x', 15, 15, 0)):
        err(V, 'each deck must have 3 items', [bad])
    for bad in NS:
        err(T, 'deck must be an exact string', [(bad, 15, 15)])
    for bad in BAD:
        err(V, NM, [(bad, 15, 15)])
    for bad in NI:
        err(T, 'slides must be an exact integer', [('x', bad, 15)])
        err(T, 'minutes must be an exact integer', [('x', 15, bad)])
    for bad in (-1, 41, -100, 10**9):
        err(V, 'slides must be 0 to 40', [('x', bad, 15)])
    for bad in (-1, 61, -100, 10**9):
        err(V, 'minutes must be 0 to 60', [('x', 15, bad)])


def _order(err):
    err(T, 'decks must be an exact list', 'x')
    err(V, 'deck count must be at most 40', [None] * 41)
    err(T, 'each deck must be an exact tuple', [None, ('x',)])
    err(V, 'each deck must have 3 items', [('x',), None])
    err(T, 'deck must be an exact string', [(5, -1, -1)])
    err(V, NM, [('A', -1, -1)])
    err(T, 'slides must be an exact integer', [('x', '0', -1)])
    err(V, 'slides must be 0 to 40', [('x', -1, -1)])
    err(T, 'minutes must be an exact integer', [('x', 0, '0')])
    err(V, 'minutes must be 0 to 60', [('x', 0, -1)])
    err(T, 'deck must be an exact string', [('x', 15, 15), (5, 15, 15)])
    err(T, 'slides must be an exact integer', [('x', 15, 15), ('x', '0', 15)])
    err(T, 'minutes must be an exact integer', [('x', 15, 15), ('x', 15, '0')])


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
