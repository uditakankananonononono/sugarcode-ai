import random
import pytest
from sugarcode.extra_doc.technical_seo import check_urls as cu

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


def oracle(urls):
    # written from the stated rule: segments drop empty parts; folded = segments lowercased, rejoined
    probs = [(i, 'relative') for i, u in enumerate(urls) if not u.startswith('/')]
    probs += [(i, 'double_slash') for i, u in enumerate(urls) if '//' in u]
    probs += [(i, 'too_deep') for i, u in enumerate(urls) if len([p for p in u.split('/') if p]) > 4]
    probs += [(i, 'uppercase') for i, u in enumerate(urls) if any(c.isupper() and 'A' <= c <= 'Z' for c in u)]
    folds = ['/' + '/'.join(p.lower() for p in u.split('/') if p) for u in urls]
    probs += [(i, 'repeat') for i in range(len(urls)) if folds[i] in folds[:i]]
    deepest = max([len([p for p in u.split('/') if p]) for u in urls] + [0])
    return {'problems': sorted(probs), 'deepest': deepest, 'total': len(urls)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied strings against one fixed style. It does not say the site is '
              'crawlable, that four levels is the right cap, or that flat paths rank better. No clinical or wet-lab '
              'claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.technical_seo as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert cu([]) == {'problems': [], 'deepest': 0, 'total': 0}
    assert cu(['/a/b']) == {'problems': [], 'deepest': 2, 'total': 1}
    assert cu(['a/b'])['problems'] == [(0, 'relative')]
    assert cu(['/a//b'])['problems'] == [(0, 'double_slash')]
    assert cu(['/a/b/c/d'])['problems'] == []
    assert cu(['/a/b/c/d/e'])['problems'] == [(0, 'too_deep')]
    assert cu(['/A/b'])['problems'] == [(0, 'uppercase')]
    assert cu(['/a/B'])['problems'] == [(0, 'uppercase')]
    assert cu(['/Z'])['problems'] == [(0, 'uppercase')]
    assert cu(['/café'])['problems'] == []                              # non-ASCII is not A-Z uppercase
    assert cu(['/a/b', '/A/B'])['problems'] == [(1, 'repeat'), (1, 'uppercase')]
    assert cu(['/a/b', '/a/b/'])['problems'] == [(1, 'repeat')]          # trailing part is empty, dropped
    assert cu(['/'])['problems'] == [] and cu(['/'])['deepest'] == 0
    assert cu(['//a'])['problems'] == [(0, 'double_slash')]
    assert cu(['/日本語/ページ'])['deepest'] == 2


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4120 + part)
    seen, clean = set(), 0
    parts = ['a', 'b', 'C', 'seo', 'Tools', 'café', '日本', 'x', 'Z', 'zeta']
    pool = []
    for _ in range(10):
        n = rnd.randint(1, 6)
        u = '/' + '/'.join(rnd.choice(parts) for _ in range(n))
        pool.append(u)
    for _ in range(60):
        urls = []
        for _ in range(rnd.randint(0, 7)):
            u = rnd.choice(pool) if rnd.random() < 0.5 else '/' + '/'.join(rnd.choice(parts) for _ in range(rnd.randint(1, 6)))
            if rnd.random() < 0.2:
                u = u.lstrip('/')
            if rnd.random() < 0.15:
                u = u.replace('/', '//', 1)
            if rnd.random() < 0.1:
                u += '/'
            urls.append(u[:120] or '/x')
        r = cu(urls)
        assert r == oracle(urls)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert len(seen) == 5 and clean >= 2


def test_limits_accepted():
    urls = ['/p%02d' % k for k in range(40)]
    r = cu(urls)
    assert r['problems'] == [] and r['total'] == 40 and r['deepest'] == 1
    cu(['/' + 'x' * 119])


def err(exc, msg, urls):
    with pytest.raises(exc) as e:
        cu(urls)
    assert str(e.value) == msg


UL = 'url length must be 1 to 120 characters'


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'urls must be an exact list', bad)
    err(V, 'url count must be at most 40', ['/x'] * 41)
    for bad in (None, 5, b'/a', StrSub('/a'), ['/a'], ('/a',)):
        err(T, 'each url must be an exact string', [bad])
    for bad in ('', 'x' * 121):
        err(V, UL, [bad])


def _order(err):
    err(T, 'urls must be an exact list', 'x')
    err(V, 'url count must be at most 40', [None] * 41)
    err(T, 'each url must be an exact string', [None, ''])
    err(V, UL, ['', None])
    err(T, 'each url must be an exact string', ['/ok', 5])
    err(V, UL, ['/ok', 'x' * 121])


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
