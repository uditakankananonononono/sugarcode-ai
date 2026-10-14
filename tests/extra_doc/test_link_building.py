import random
import pytest
from sugarcode.extra_doc.link_building import check_links as cl

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


THIN = {'click here', 'here', 'link', 'read more'}


def oracle(links):
    # written from the stated rule: self link; same pair as earlier; anchor over 60; folded anchor in the thin table
    probs = [(i, 'self_link') for i, (s, t, _) in enumerate(links) if s == t]
    pairs = [(s, t) for s, t, _ in links]
    probs += [(i, 'repeat') for i in range(len(links)) if pairs[i] in pairs[:i]]
    probs += [(i, 'anchor_long') for i, (_, _, a) in enumerate(links) if len(a) > 60]
    probs += [(i, 'thin_anchor') for i, (_, _, a) in enumerate(links) if ' '.join(a.lower().split()) in THIN]
    targets = sorted({t for _, t, _ in links})
    tmap = {t: len({s for s, tt, _ in links if tt == t}) for t in targets}
    return {'problems': sorted(probs), 'targets': tmap, 'total': len(links)}


DISCLAIMER = ('NOT_CLAIMED: this checks a supplied table. It does not say the links exist, that thin anchors hurt, '
              'or that any link passes value. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.link_building as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    good = [('blog_a', 'mysite', 'a great guide'), ('news_b', 'mysite', 'coverage')]
    assert cl(good) == {'problems': [], 'targets': {'mysite': 2}, 'total': 2}
    assert cl([]) == {'problems': [], 'targets': {}, 'total': 0}
    assert cl([('a', 'a', 'x')])['problems'] == [(0, 'self_link')]
    assert cl([('a', 'b', 'x'), ('a', 'b', 'y')])['problems'] == [(1, 'repeat')]
    assert cl([('a', 'b', 'x'), ('b', 'a', 'x')])['problems'] == []      # swapped pair is a different pair
    assert cl([('a', 'b', 'x' * 60)])['problems'] == []
    assert cl([('a', 'b', 'x' * 61)])['problems'] == [(0, 'anchor_long')]
    assert cl([('a', 'b', 'click here')])['problems'] == [(0, 'thin_anchor')]
    assert cl([('a', 'b', 'Click  Here')])['problems'] == [(0, 'thin_anchor')]   # folded
    assert cl([('a', 'b', 'click here now')])['problems'] == []
    assert cl([('a', 'b', 'café guide')])['problems'] == []
    assert cl([('a', 'b', '日本語ガイド')])['problems'] == []
    r = cl([('a', 't', 'one'), ('b', 't', 'two'), ('a', 't', 'three'), ('c', 'u', 'four')])
    assert r['problems'] == [(2, 'repeat')] and r['targets'] == {'t': 2, 'u': 1}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4110 + part)
    seen, clean = set(), 0
    anchors = ['good guide', 'click here', 'HERE', 'read  more', 'café', '日本語', 'x' * 61, 'link', 'deep dive']
    for _ in range(60):
        links = []
        for _ in range(rnd.randint(0, 7)):
            links.append((rnd.choice('abc'), rnd.choice('abc'), rnd.choice(anchors)))
        r = cl(links)
        assert r == oracle(links)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert len(seen) == 4 and clean >= 2


def test_limits_accepted():
    links = [('s%02d' % k, 't%d' % (k % 5), 'anchor %d' % k) for k in range(30)]
    r = cl(links)
    assert r['problems'] == [] and r['total'] == 30 and len(r['targets']) == 5
    cl([('a' * 24, 'b' * 24, 'x' * 80)])


def err(exc, msg, links):
    with pytest.raises(exc) as e:
        cl(links)
    assert str(e.value) == msg


SM = 'source must be 1 to 24 lowercase identifier characters'
TM = 'target must be 1 to 24 lowercase identifier characters'
AL = 'anchor length must be 1 to 80 characters'
NS = (None, 5, b'a', StrSub('a'))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'links must be an exact list', bad)
    err(V, 'link count must be at most 30', [('a', 'b', 'x')] * 31)
    for bad in (None, ['a', 'b', 'x'], 'ab', TupleSub(('a', 'b', 'x')), 5):
        err(T, 'each link must be an exact tuple', [bad])
    for bad in ((), ('a', 'b'), ('a', 'b', 'x', 1)):
        err(V, 'each link must have 3 items', [bad])
    for bad in NS:
        err(T, 'source must be an exact string', [(bad, 'b', 'x')])
        err(T, 'target must be an exact string', [('a', bad, 'x')])
    for bad in BAD:
        err(V, SM, [(bad, 'b', 'x')])
        err(V, TM, [('a', bad, 'x')])
    for bad in NS:
        err(T, 'anchor must be an exact string', [('a', 'b', bad)])
    for bad in ('', 'x' * 81):
        err(V, AL, [('a', 'b', bad)])


def _order(err):
    err(T, 'links must be an exact list', 'x')
    err(V, 'link count must be at most 30', [None] * 31)
    err(T, 'each link must be an exact tuple', [None, ('a',)])
    err(V, 'each link must have 3 items', [('a',), None])
    err(T, 'source must be an exact string', [(5, 'A', 5)])
    err(V, SM, [('A', 5, 5)])
    err(T, 'target must be an exact string', [('a', 5, 5)])
    err(V, TM, [('a', 'A', 5)])
    err(T, 'anchor must be an exact string', [('a', 'b', 5)])
    err(V, AL, [('a', 'b', '')])
    err(T, 'source must be an exact string', [('a', 'b', 'x'), (5, 'b', 'x')])
    err(T, 'target must be an exact string', [('a', 'b', 'x'), ('a', 5, 'x')])


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
