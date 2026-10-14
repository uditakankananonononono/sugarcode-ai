import random
import pytest
from sugarcode.extra_doc.sales_script_development import check_beats as cb

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


PHASES = ('opening', 'discovery', 'pitch', 'close')


def oracle(beats):
    # written from the stated rule: below the furthest earlier rank is phase_back, over one above is phase_skip
    probs = []
    furthest = -1
    for i, (_, p) in enumerate(beats):
        rank = PHASES.index(p)
        if rank < furthest:
            probs.append((i, 'phase_back'))
        elif rank > furthest + 1:
            probs.append((i, 'phase_skip'))
        furthest = max(furthest, rank)
    return {'problems': sorted(probs), 'beats': sorted({b for b, _ in beats}), 'total': len(beats)}


DISCLAIMER = ('NOT_CLAIMED: this checks a supplied beat list against one phase-order rule. It does not say the '
              'script structures a good pitch, that the four phases are the right model, or that any pitch was '
              'delivered. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.sales_script_development as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert cb([]) == {'problems': [], 'beats': [], 'total': 0}
    assert cb([('b', 'opening')]) == {'problems': [], 'beats': ['b'], 'total': 1}
    assert cb([('b', 'discovery')])['problems'] == [(0, 'phase_skip')]
    assert cb([('b', 'close')])['problems'] == [(0, 'phase_skip')]
    assert cb([('a', 'opening'), ('b', 'pitch')])['problems'] == [(1, 'phase_skip')]
    assert cb([('a', 'pitch'), ('b', 'discovery')])['problems'] == [(0, 'phase_skip'), (1, 'phase_back')]
    assert cb([('a', 'close'), ('b', 'opening')])['problems'] == [(0, 'phase_skip'), (1, 'phase_back')]
    assert cb([('a', 'opening'), ('b', 'discovery'), ('c', 'pitch'), ('d', 'close')])['problems'] == []
    assert cb([('a', 'opening'), ('b', 'opening'), ('c', 'discovery')])['problems'] == []
    assert cb([('a', 'discovery'), ('b', 'opening')])['problems'] == [(0, 'phase_skip'), (1, 'phase_back')]
    assert cb([('a', 'opening'), ('b', 'close'), ('c', 'pitch')])['problems'] == [(1, 'phase_skip'), (2, 'phase_back')]
    assert cb([('b', 'opening'), ('a', 'opening')]) == {'problems': [], 'beats': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4300 + part)
    seen, clean = set(), 0
    for _ in range(60):
        beats = []
        for _ in range(rnd.randint(0, 9)):
            beats.append((rnd.choice(('b1', 'b2', 'b3')), rnd.choice(PHASES)))
        r = cb(beats)
        assert r == oracle(beats)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'phase_back', 'phase_skip'} and clean >= 2


def test_limits_accepted():
    beats = [('b%02d' % k, 'opening') for k in range(40)]
    r = cb(beats)
    assert r['total'] == 40 and r['problems'] == []
    assert cb([('a' * 24, 'close')])['problems'] == [(0, 'phase_skip')]
    cb([('a', 'opening')])


def err(exc, msg, beats):
    with pytest.raises(exc) as e:
        cb(beats)
    assert str(e.value) == msg


BM = 'beat must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'beats must be an exact list', bad)
    err(V, 'beat count must be at most 40', [('b', 'opening')] * 41)
    for bad in (None, ['b', 'opening'], 'ab', TupleSub(('b', 'opening')), 5):
        err(T, 'each beat must be an exact tuple', [bad])
    for bad in ((), ('b',), ('b', 'opening', 0)):
        err(V, 'each beat must have 2 items', [bad])
    for bad in NS:
        err(T, 'beat must be an exact string', [(bad, 'opening')])
        err(T, 'phase must be an exact string', [('b', bad)])
    for bad in BAD:
        err(V, BM, [(bad, 'opening')])
    for bad in ('', 'Opening', 'OPENING', 'open', 'close ', 'pitch0', 'discovery\n', 'clöse'):
        err(V, 'phase must be opening, discovery, pitch or close', [('b', bad)])


def _order(err):
    err(T, 'beats must be an exact list', 'x')
    err(V, 'beat count must be at most 40', [None] * 41)
    err(T, 'each beat must be an exact tuple', [None, ('b',)])
    err(V, 'each beat must have 2 items', [('b',), None])
    err(T, 'beat must be an exact string', [(5, 'x')])
    err(V, BM, [('A', 'x')])
    err(T, 'phase must be an exact string', [('b', 5)])
    err(V, 'phase must be opening, discovery, pitch or close', [('b', 'x')])
    err(T, 'beat must be an exact string', [('b', 'opening'), (5, 'opening')])
    err(T, 'phase must be an exact string', [('b', 'opening'), ('b', 5)])


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
