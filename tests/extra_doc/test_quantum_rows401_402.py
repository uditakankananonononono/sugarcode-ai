import random
import pytest
from sugarcode.extra_doc.targeting_strategy import check_targets as ct
from sugarcode.extra_doc.positioning_strategy import check_positions as cp

T, V = TypeError, ValueError


class StrSub(str):
    pass


class IntSub(int):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


def oracle_t(segs):
    # independent: per-segment rule dict, then a stable sort by negated score
    probs, scores, elig, names = [], [], [], []
    for i, (n, s, f) in enumerate(segs):
        codes = []
        if s < 100: codes.append('too_small')
        if f < 60: codes.append('low_fit')
        if n in names: codes.append('same_name')
        names.append(n)
        probs += [(i, c) for c in codes]
        scores.append(s * f)
        if not codes: elig.append((-s * f, i, n))
    return {'problems': sorted(probs), 'scores': scores,
            'targets': [n for _, _, n in sorted(elig)], 'total_size': sum(x[1] for x in segs)}


def oracle_p(attrs):
    out = {'problems': [], 'verdicts': [], 'margins': [], 'wins': [], 'net': 0}
    for i, (n, o, r) in enumerate(attrs):
        d = o - r
        out['margins'].append(d)
        out['net'] += d
        v = 'tie'
        if d > 1: v = 'win'; out['wins'].append(n)
        if d < -1: v = 'lag'
        out['verdicts'].append(v)
        if n in [a[0] for a in attrs[:i]]: out['problems'].append((i, 'same_attribute'))
    out['wins'].sort()
    return out


def test_hand_t():
    assert ct([]) == {'problems': [], 'scores': [], 'targets': [], 'total_size': 0}
    assert ct([('a', 100, 60)]) == {'problems': [], 'scores': [6000], 'targets': ['a'], 'total_size': 100}
    assert ct([('a', 99, 60)])['problems'] == [(0, 'too_small')]
    assert ct([('a', 100, 59)])['problems'] == [(0, 'low_fit')]
    assert ct([('a', 5, 5)])['problems'] == [(0, 'low_fit'), (0, 'too_small')]
    r = ct([('a', 200, 70), ('b', 100, 140 - 40), ('a', 500, 90)])
    assert r['problems'] == [(2, 'same_name')] and r['targets'] == ['a', 'b']
    r = ct([('x', 100, 70), ('y', 100, 70), ('z', 200, 70)])
    assert r['targets'] == ['z', 'x', 'y']
    assert ct([('a', 1000000, 100)])['scores'] == [100000000]


def test_hand_p():
    assert cp([]) == {'problems': [], 'verdicts': [], 'margins': [], 'wins': [], 'net': 0}
    r = cp([('a', 5, 3), ('b', 3, 5), ('c', 4, 3), ('d', 3, 4), ('e', 10, 0), ('f', 0, 10)])
    assert r['verdicts'] == ['win', 'lag', 'tie', 'tie', 'win', 'lag']
    assert r['margins'] == [2, -2, 1, -1, 10, -10] and r['net'] == 0 and r['wins'] == ['a', 'e']
    assert cp([('a', 1, 1), ('a', 9, 0)])['problems'] == [(1, 'same_attribute')]


@pytest.mark.parametrize('part', range(4))
def test_random(part):
    rnd = random.Random(40100 + part)
    for _ in range(80):
        names = ['a', 'b', 'c', 'd', 'e_1']
        segs = [(rnd.choice(names), rnd.choice([1, 99, 100, 101, 5000, 1000000]), rnd.choice([0, 59, 60, 61, 100]))
                for _ in range(rnd.randint(0, 12))]
        assert ct(segs) == oracle_t(segs)
        at = [(rnd.choice(names), rnd.randint(0, 10), rnd.randint(0, 10)) for _ in range(rnd.randint(0, 10))]
        assert cp(at) == oracle_p(at)


def e(fn, exc, msg, arg):
    with pytest.raises(exc) as x:
        fn(arg)
    assert str(x.value) == msg


def test_pins_t():
    for b in (None, (), 'ab', ListSub([]), {}):
        e(ct, T, 'segments must be an exact list', b)
    e(ct, V, 'segment count must be at most 12', [('a', 1, 1)] * 13)
    e(ct, V, 'segment count must be at most 12', [None] * 13)
    for b in (None, ['a', 1, 1], TupleSub(('a', 1, 1))):
        e(ct, T, 'each segment must be an exact tuple', [b])
    for b in ((), ('a', 1), ('a', 1, 1, 1)):
        e(ct, V, 'each segment must have 3 items', [b])
    for b in (None, 5, b'a', StrSub('a')):
        e(ct, T, 'name must be an exact string', [(b, 1, 1)])
    for b in ('', 'A', '1a', 'a' * 25, 'é'):
        e(ct, V, 'name must be 1 to 24 lowercase identifier characters', [(b, 1, 1)])
    ct([('a' * 24, 1, 1)])
    for b in (None, 1.0, True, IntSub(1), '1'):
        e(ct, T, 'size must be an exact int', [('a', b, 1)])
    for b in (0, -1, 1000001):
        e(ct, V, 'size must be 1 to 1000000', [('a', b, 1)])
    for b in (None, 1.0, False, IntSub(1)):
        e(ct, T, 'fit must be an exact int', [('a', 1, b)])
    for b in (-1, 101):
        e(ct, V, 'fit must be 0 to 100', [('a', 1, b)])
    e(ct, T, 'each segment must be an exact tuple', [('a', 1, 1), None, 5])
    e(ct, V, 'size must be 1 to 1000000', [('a', 0, 1000)])
    e(ct, T, 'size must be an exact int', [('A', 'x', 1)] if False else [('a', 'x', 200)])
    e(ct, V, 'name must be 1 to 24 lowercase identifier characters', [('A', 'x', 1)])


def test_pins_p():
    for b in (None, (), 'ab', ListSub([]), {}):
        e(cp, T, 'attrs must be an exact list', b)
    e(cp, V, 'attribute count must be at most 10', [('a', 1, 1)] * 11)
    for b in (None, ['a', 1, 1], TupleSub(('a', 1, 1))):
        e(cp, T, 'each attribute must be an exact tuple', [b])
    for b in ((), ('a', 1), ('a', 1, 1, 1)):
        e(cp, V, 'each attribute must have 3 items', [b])
    for b in (None, 5, StrSub('a')):
        e(cp, T, 'attribute must be an exact string', [(b, 1, 1)])
    for b in ('', 'A', 'a' * 25):
        e(cp, V, 'attribute must be 1 to 24 lowercase identifier characters', [(b, 1, 1)])
    for b in (None, 1.0, True, IntSub(1)):
        e(cp, T, 'ours must be an exact int', [('a', b, 1)])
        e(cp, T, 'rival must be an exact int', [('a', 1, b)])
    for b in (-1, 11):
        e(cp, V, 'ours must be 0 to 10', [('a', b, 1)])
        e(cp, V, 'rival must be 0 to 10', [('a', 1, b)])
    e(cp, T, 'ours must be an exact int', [('a', 'x', 99)])


BADLABELS = ['_a', 'a-b', 'a b', 'a.b', 'a\n', ' a', 'a ', 'a\x00', '\uff41', 'a1-', 'a/b', '9a']


def test_label_charset_witnesses():
    for b in BADLABELS:
        e(ct, V, 'name must be 1 to 24 lowercase identifier characters', [(b, 200, 70)])
        e(cp, V, 'attribute must be 1 to 24 lowercase identifier characters', [(b, 1, 1)])
    for g in ('a_', 'a1', 'z9_', 'a' * 24):
        ct([(g, 200, 70)])
        cp([(g, 1, 1)])


def test_subclass_refusal_everywhere():
    e(ct, T, 'name must be an exact string', [(StrSub('a'), 200, 70)])
    e(ct, T, 'size must be an exact int', [('a', IntSub(200), 70)])
    e(ct, T, 'fit must be an exact int', [('a', 200, IntSub(70))])
    e(cp, T, 'attribute must be an exact string', [(StrSub('a'), 1, 1)])
    e(cp, T, 'ours must be an exact int', [('a', IntSub(1), 1)])
    e(cp, T, 'rival must be an exact int', [('a', 1, IntSub(1))])
    e(ct, T, 'each segment must be an exact tuple', [TupleSub(('a', 200, 70))])
    e(cp, T, 'attrs must be an exact list', ListSub())
    e(ct, T, 'segments must be an exact list', ListSub())
