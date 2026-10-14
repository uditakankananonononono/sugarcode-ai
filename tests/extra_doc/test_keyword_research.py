import random
import pytest
from sugarcode.extra_doc.keyword_research import check_keywords as ck

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


def oracle(terms):
    # written from the stated rule: folded = words lowercased and joined by single spaces
    folds = [' '.join(t.lower().split()) for t in terms]
    probs = [(i, 'messy') for i, t in enumerate(terms) if t != folds[i]]
    probs += [(i, 'repeat') for i in range(len(terms)) if folds[i] in folds[:i]]
    probs += [(i, 'thin') for i, t in enumerate(terms) if len(t) < 3]
    for i in range(len(terms)):
        w = set(folds[i].split())
        if any(w and w < set(folds[j].split()) for j in range(i)):
            probs.append((i, 'covered'))
    seen = sorted(set(folds))
    return {'problems': sorted(probs), 'folded': seen,
            'words': len({w for f in seen for w in f.split()}), 'total': len(terms)}


DISCLAIMER = ('NOT_CLAIMED: this tidies a supplied list. It does not say the keywords get searched, that coverage is '
              'bad, or that any of them ranks. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.keyword_research as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'folded': [], 'words': 0, 'total': 0}
    assert ck(['seo tools']) == {'problems': [], 'folded': ['seo tools'], 'words': 2, 'total': 1}
    assert ck(['SEO'])['problems'] == [(0, 'messy')]
    assert ck(['seo  tools'])['problems'] == [(0, 'messy')]
    assert ck([' seo'])['problems'] == [(0, 'messy')]
    assert ck(['seo', 'SEO'])['problems'] == [(1, 'messy'), (1, 'repeat')]
    assert ck(['ab'])['problems'] == [(0, 'thin')]
    assert ck(['abc'])['problems'] == []
    assert ck(['seo tools', 'seo'])['problems'] == [(1, 'covered')]
    assert ck(['seo tools', 'tools'])['problems'] == [(1, 'covered')]
    assert ck(['seo tools', 'tools seo'])['problems'] == []             # same words, not fewer
    assert ck(['best seo tools', 'seo', 'best'])['problems'] == [(1, 'covered'), (2, 'covered')]
    assert ck(['café', 'café'])['problems'] == [(1, 'repeat')]
    assert ck(['日本語', '日本'])['problems'] == [(1, 'thin')]          # 2 characters; not covered: different words
    assert ck(['日本語会話', '日本語'])['problems'] == []              # one word each, not a subset pair
    assert ck(['café tools', 'café'])['problems'] == [(1, 'covered')]
    assert ck(['ＳＥＯ'])['problems'] == [(0, 'messy')]                  # lower() folds fullwidth, so messy
    r = ck(['a b c', 'a b', 'b c'])
    assert r['problems'] == [(1, 'covered'), (2, 'covered')] and r['words'] == 3


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4100 + part)
    seen, clean = set(), 0
    bag = ['seo', 'tools', 'SEO', 'best', 'guide', 'café', '日本', 'ab', 'a', 'x9', 'ＳＥＯ']
    for _ in range(60):
        terms = []
        for _ in range(rnd.randint(0, 8)):
            n = rnd.randint(1, 3)
            t = ' '.join(rnd.choice(bag) for _ in range(n))
            if rnd.random() < 0.2:
                t = ' ' + t if rnd.random() < 0.5 else t + '  '
            terms.append(t[:40])
        r = ck(terms)
        assert r == oracle(terms)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert len(seen) == 4 and clean >= 2


def test_limits_accepted():
    terms = ['kw%02d' % k for k in range(50)]
    r = ck(terms)
    assert r['problems'] == [] and r['total'] == 50 and r['words'] == 50
    ck(['x' * 40])


def err(exc, msg, terms):
    with pytest.raises(exc) as e:
        ck(terms)
    assert str(e.value) == msg


TL = 'term length must be 1 to 40 characters'


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'terms must be an exact list', bad)
    err(V, 'term count must be at most 50', ['ok'] * 51)
    for bad in (None, 5, b'a', StrSub('a'), ['a'], ('a',)):
        err(T, 'each term must be an exact string', [bad])
    for bad in ('', 'x' * 41):
        err(V, TL, [bad])


def _order(err):
    err(T, 'terms must be an exact list', 'x')
    err(V, 'term count must be at most 50', [None] * 51)
    err(T, 'each term must be an exact string', [None, ''])
    err(V, TL, ['', None])
    err(T, 'each term must be an exact string', ['ok', 5])
    err(V, TL, ['ok', 'x' * 41])


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
