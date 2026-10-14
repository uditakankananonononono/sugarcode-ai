import random
import pytest
from sugarcode.extra_doc.segmentation_analysis import check_segments as cs

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


def oracle(segments):
    # written from the stated rule: "shared" ids appear in two or more distinct segments
    probs = [(i, 'same_name') for i in range(len(segments)) if segments[i][0] in [s[0] for s in segments[:i]]]
    probs += [(i, 'empty') for i, (_, ms) in enumerate(segments) if len(ms) == 0]
    probs += [(i, 'below_floor') for i, (_, ms) in enumerate(segments) if 0 < len(ms) < 4]
    probs += [(i, 'repeat') for i, (_, ms) in enumerate(segments) if len(set(ms)) != len(ms)]
    earlier = [set().union(*[set(ms) for _, ms in segments[:i]], set()) if i else set() for i in range(len(segments))]
    probs += [(i, 'overlap') for i, (_, ms) in enumerate(segments) if earlier[i] & set(ms)]
    sizes = sorted((nm, len(ms)) for nm, ms in segments)
    everyone = {m for _, ms in segments for m in ms}
    shared = sorted(m for m in everyone if sum(1 for _, ms in segments if m in set(ms)) >= 2)
    return {'problems': sorted(probs), 'sizes': sizes, 'shared': shared, 'total': len(everyone)}


DISCLAIMER = ('NOT_CLAIMED: this checks a supplied table. It does not say the segments are meaningful, that the '
              'floor of 4 fits the market, or that dividing customers this way helps. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.segmentation_analysis as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    good = [('a', ['m1', 'm2', 'm3', 'm4']), ('b', ['n1', 'n2', 'n3', 'n4'])]
    assert cs(good) == {'problems': [], 'sizes': [('a', 4), ('b', 4)], 'shared': [], 'total': 8}
    assert cs([]) == {'problems': [], 'sizes': [], 'shared': [], 'total': 0}
    assert cs([('a', [])])['problems'] == [(0, 'empty')]
    assert cs([('a', ['m1'])])['problems'] == [(0, 'below_floor')]
    assert cs([('a', ['m1', 'm2', 'm3'])])['problems'] == [(0, 'below_floor')]
    assert cs([('a', ['m1', 'm2', 'm3', 'm4'])])['problems'] == []
    assert cs([('a', ['m', 'm'])])['shared'] == []          # repeated inside one segment is not shared
    assert cs([('a', ['m', 'm']), ('b', ['m'])])['shared'] == ['m']
    assert cs([('a', ['m1', 'm1', 'm2', 'm3'])])['problems'] == [(0, 'repeat')]
    r = cs([('a', ['m1', 'm2', 'm3', 'm4']), ('b', ['m4', 'm5', 'm6', 'm7'])])
    assert r['problems'] == [(1, 'overlap')] and r['shared'] == ['m4'] and r['total'] == 7
    assert cs([('a', ['m1', 'm2', 'm3', 'm4']), ('a', ['n1', 'n2', 'n3', 'n4'])])['problems'] == [(1, 'same_name')]
    assert cs([('b', ['m1']), ('a', ['m1'])])['problems'] == [(0, 'below_floor'), (1, 'below_floor'), (1, 'overlap')]
    r = cs([('a', ['m1', 'm2', 'm3', 'm4']), ('b', ['m4', 'm1', 'm5', 'm6']), ('c', ['m4'])])
    assert r['shared'] == ['m1', 'm4'] and r['sizes'] == [('a', 4), ('b', 4), ('c', 1)]


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4000 + part)
    seen, clean = set(), 0
    pool = ['m%d' % k for k in range(12)]
    for _ in range(60):
        segs = []
        for j in range(rnd.randint(0, 5)):
            nm = rnd.choice('abc')
            ms = [rnd.choice(pool) for _ in range(rnd.randint(0, 6))]
            segs.append((nm, ms))
        r = cs(segs)
        assert r == oracle(segs)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert len(seen) == 5 and clean > 3


def test_limits_accepted():
    segs = [('s%02d' % i, ['m%02d_%d' % (i, k) for k in range(50)]) for i in range(12)]
    r = cs(segs)
    assert r['problems'] == [] and r['total'] == 600 and len(r['sizes']) == 12
    cs([('a' * 24, ['b' * 24])])


def err(exc, msg, segments):
    with pytest.raises(exc) as e:
        cs(segments)
    assert str(e.value) == msg


NM = 'name must be 1 to 24 lowercase identifier characters'
MM = 'member must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'segments must be an exact list', bad)
    err(V, 'segment count must be at most 12', [('a', [])] * 13)
    for bad in (None, ['a', []], 'ab', TupleSub(('a', [])), 5):
        err(T, 'each segment must be an exact tuple', [bad])
    for bad in ((), ('a',), ('a', [], 1)):
        err(V, 'each segment must have 2 items', [bad])
    for bad in NS:
        err(T, 'name must be an exact string', [(bad, [])])
    for bad in BAD:
        err(V, NM, [(bad, [])])
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'members must be an exact list', [('a', bad)])
    err(V, 'member count must be at most 50', [('a', ['m%d' % k for k in range(51)])])
    for bad in NS:
        err(T, 'member must be an exact string', [('a', [bad])])
    for bad in BAD:
        err(V, MM, [('a', [bad])])


def _order(err):
    err(T, 'segments must be an exact list', 'x')
    err(V, 'segment count must be at most 12', [None] * 13)
    err(T, 'each segment must be an exact tuple', [None, ('a',)])
    err(V, 'each segment must have 2 items', [('a',), None])
    err(T, 'name must be an exact string', [(5, 'x')])
    err(V, NM, [('A', 5)])
    err(T, 'members must be an exact list', [('a', 5)])
    err(V, 'member count must be at most 50', [('a', ['m%d' % k for k in range(51)]), ('b', 5)])
    err(T, 'member must be an exact string', [('a', [5, 'A'])])
    err(V, MM, [('a', ['A', 5])])
    err(T, 'name must be an exact string', [('a', []), (5, 'x')])


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
