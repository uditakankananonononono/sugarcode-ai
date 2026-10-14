import random
import pytest
from sugarcode.extra_doc.brand_architecture import check_brands as cb
from sugarcode.extra_doc.brand_voice import check_voice as cv

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


def oracle_b(brands):
    probs, first = [], {}
    names = [n for n, _ in brands]
    for i, (n, p) in enumerate(brands):
        if n in names[:i]:
            probs.append((i, 'same_name'))
        else:
            first[n] = p
        if p is not None and p == n:
            probs.append((i, 'self_parent'))
        elif p is not None and p not in names:
            probs.append((i, 'missing_parent'))
    depths = {}
    for n in first:
        path, cur = [], n
        while True:
            if cur in path or cur not in first:
                break
            path.append(cur)
            if first[cur] is None:
                depths[n] = len(path) - 1
                break
            cur = first[cur]
    return {'problems': sorted(probs), 'roots': [n for n, p in brands if p is None],
            'depths': sorted(depths.items()), 'max_depth': max(depths.values()) if depths else 0}


def oracle_v(avoid, lines):
    probs, hits, words, seen = [], {}, 0, []
    for i, s in enumerate(lines):
        toks = []
        for t in s.split(' '):
            if not t:
                continue
            t = t.translate({c: c + 32 for c in range(65, 91)})
            t = t.rstrip('.,!?')
            toks.append(t)
        words += len(toks)
        if any(t in avoid for t in toks):
            probs.append((i, 'avoided_word'))
        for t in toks:
            if t in avoid:
                hits[t] = hits.get(t, 0) + 1
        if len(toks) < 3:
            probs.append((i, 'too_short'))
        if toks in seen:
            probs.append((i, 'repeat'))
        seen.append(toks)
    return {'problems': sorted(probs), 'hits': sorted(hits.items()), 'words': words}


def test_hand_b():
    assert cb([]) == {'problems': [], 'roots': [], 'depths': [], 'max_depth': 0}
    r = cb([('a', None), ('b', 'a'), ('c', 'b'), ('x', 'y'), ('y', 'x'), ('s', 's'), ('a', None), ('m', 'q')])
    assert r['problems'] == [(5, 'self_parent'), (6, 'same_name'), (7, 'missing_parent')]
    assert r['depths'] == [('a', 0), ('b', 1), ('c', 2)] and r['max_depth'] == 2 and r['roots'] == ['a', 'a']
    assert cb([('a', 'a')])['depths'] == [] and cb([('a', None)])['depths'] == [('a', 0)]
    chain = [('n0', None)] + [('n%d' % i, 'n%d' % (i - 1)) for i in range(1, 20)]
    assert cb(chain)['max_depth'] == 19


def test_hand_v():
    assert cv([], []) == {'problems': [], 'hits': [], 'words': 0}
    r = cv(['cheap'], ['Buy CHEAP now!', 'hi  there', 'hi there', 'Hi there.', 'x y z'])
    assert r['problems'] == [(0, 'avoided_word'), (1, 'too_short'), (2, 'repeat'), (2, 'too_short'),
                             (3, 'repeat'), (3, 'too_short')]
    assert r['hits'] == [('cheap', 1)] and r['words'] == 12
    assert cv(['a'], ['a a a a'])['hits'] == [('a', 4)]
    assert cv(['abc'], ['ÀBC ABC ok'])['hits'] == [('abc', 1)]
    assert cv(['cheap'], ['cheap!!. is ok'])['hits'] == [('cheap', 1)]
    assert cv([], ['a b c'])['problems'] == []
    assert cv(['zzz', 'aaa'], ['ZZZ AAA @@@', '[[[ `` {{'])['hits'] == [('aaa', 1), ('zzz', 1)]
    assert cv(['at'], ['@ @ AT'])['hits'] == [('at', 1)]


@pytest.mark.parametrize('part', range(4))
def test_random(part):
    rnd = random.Random(40300 + part)
    pool = ['a', 'b', 'c', 'd', 'e']
    for _ in range(100):
        bs = [(rnd.choice(pool), rnd.choice(pool + [None, None])) for _ in range(rnd.randint(0, 20))]
        assert cb(bs) == oracle_b(bs)
        av = rnd.sample(['cheap', 'best', 'ok'], rnd.randint(0, 3))
        ws = ['cheap', 'CHEAP', 'Zz', 'aZ', 'Best', 'ok.', 'ok!?', 'x', 'Zed,', 'ÀB']
        ls = [' '.join(rnd.choice(ws) for _ in range(rnd.randint(1, 6))) for _ in range(rnd.randint(0, 20))]
        assert cv(av, ls) == oracle_v(av, ls)


def e(fn, exc, msg, *a):
    with pytest.raises(exc) as x:
        fn(*a)
    assert str(x.value) == msg


def test_pins_b():
    for b in (None, (), 'ab', ListSub([]), {}):
        e(cb, T, 'brands must be an exact list', b)
    e(cb, V, 'brand count must be at most 20', [('a', None)] * 21)
    for b in (None, ['a', None], TupleSub(('a', None))):
        e(cb, T, 'each brand must be an exact tuple', [b])
    for b in ((), ('a',), ('a', None, 1)):
        e(cb, V, 'each brand must have 2 items', [b])
    for b in (None, 5, StrSub('a')):
        e(cb, T, 'name must be an exact string', [(b, None)])
    for b in ('', 'A', '1a', 'a' * 25):
        e(cb, V, 'name must be 1 to 24 lowercase identifier characters', [(b, None)])
    for b in (5, StrSub('a'), b'a'):
        e(cb, T, 'parent must be an exact string', [('a', b)])
    for b in ('', 'A', 'a' * 25):
        e(cb, V, 'parent must be 1 to 24 lowercase identifier characters', [('a', b)])
    e(cb, T, 'parent must be an exact string', [('A', 5)] if False else [('a', 5), (5, None)])
    cb([('a' * 24, 'a' * 24)])


def test_pins_v():
    for b in (None, (), 'ab', ListSub([])):
        e(cv, T, 'avoid must be an exact list', b, [])
        e(cv, T, 'lines must be an exact list', [], b)
    e(cv, V, 'avoid count must be at most 10', ['a'] * 11, [])
    for b in (None, 5, StrSub('a')):
        e(cv, T, 'avoid word must be an exact string', [b], [])
    for b in ('', 'A', 'a1', 'a' * 17, 'é'):
        e(cv, V, 'avoid word must be 1 to 16 lowercase ASCII letters', [b], [])
    e(cv, V, 'line count must be at most 20', [], ['x'] * 21)
    for b in (None, 5, StrSub('a')):
        e(cv, T, 'line must be an exact string', [], [b])
    for b in ('', 'x' * 201):
        e(cv, V, 'line length must be 1 to 200 characters', [], [b])
    cv([], ['x' * 200])
    e(cv, T, 'avoid must be an exact list', None, 5)
    e(cv, T, 'avoid word must be an exact string', [5], 5)
    e(cv, V, 'avoid word must be 1 to 16 lowercase ASCII letters', ['A'], 5)


BADLABELS = ['_a', 'a-b', 'a b', 'a.b', 'a\n', ' a', 'a ', 'a\x00', '\uff41', 'a1-', 'a/b', '9a']


def test_label_charset_witnesses():
    for b in BADLABELS:
        e(cb, V, 'name must be 1 to 24 lowercase identifier characters', [(b, None)])
        e(cb, V, 'parent must be 1 to 24 lowercase identifier characters', [('a', b)])
    for b in ['_a', 'a-b', 'a b', 'a.b', 'a\n', ' a', 'a1', 'a_', '\uff41', 'A', '\u00e9']:
        e(cv, V, 'avoid word must be 1 to 16 lowercase ASCII letters', [b], [])
    for g in ('a_', 'a1', 'z9_', 'a' * 24):
        cb([(g, g)])


def test_subclass_refusal_everywhere():
    e(cb, T, 'name must be an exact string', [(StrSub('a'), None)])
    e(cb, T, 'parent must be an exact string', [('a', StrSub('a'))])
    e(cv, T, 'avoid word must be an exact string', [StrSub('a')], [])
    e(cv, T, 'line must be an exact string', [], [StrSub('a b c')])
    e(cb, T, 'each brand must be an exact tuple', [TupleSub(('a', None))])
    e(cv, T, 'lines must be an exact list', [], ListSub())
    e(cv, T, 'avoid must be an exact list', ListSub(), [])


def test_voice_boundaries_and_fold():
    assert cv(['aa', 'bb', 'cc', 'dd', 'ee', 'ff', 'gg', 'hh', 'ii', 'jj'], []) == {'problems': [], 'hits': [], 'words': 0}
    e(cv, V, 'avoid count must be at most 10', ['aa', 'bb', 'cc', 'dd', 'ee', 'ff', 'gg', 'hh', 'ii', 'jj', 'kk'], [])
    assert cv(['a' * 16], ['a' * 16 + ' b c'])['hits'] == [('a' * 16, 1)]
    e(cv, V, 'avoid word must be 1 to 16 lowercase ASCII letters', ['a' * 17], [])
    assert cv([], ['a\tb c d'])['words'] == 3
    assert cv([], ['a\tb c'])['problems'] == [(0, 'too_short')]
    assert cv([], ['\u00c9 \u00e9 \u00e9'])['words'] == 3
    assert cv([], ['\u00c9 \u00e9 \u00e9', '\u00e9 \u00e9 \u00e9'])['problems'] == []
    assert cv([], ['\u00c9 \u00e9 \u00e9', '\u00c9 \u00e9 \u00e9'])['problems'] == [(1, 'repeat')]
    for line in ('abx q r', 'ab; q r', 'ab: q r', "ab' q r", 'ab- q r', 'ab) q r', 'ab.x q r', 'xab q r', 'ab_ q r'):
        assert cv(['ab'], [line])['hits'] == [], line
    for line in ('ab q r', 'ab. q r', 'ab, q r', 'ab! q r', 'ab? q r', 'ab?!., q r', 'AB q r'):
        assert cv(['ab'], [line])['hits'] == [('ab', 1)], line
