import random
import pytest
from sugarcode.extra_doc.content_marketing import check_assets as ca

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


STAGES = ('awareness', 'consideration', 'decision')
FORMATS = ('blog', 'video', 'guide', 'webinar', 'case_study')
MISMATCH = {('awareness', 'case_study'), ('decision', 'blog')}


def oracle(assets):
    # written from the stated rule: repeat title, title over 70, fixed mismatch table, stage gaps
    probs = [(i, 'repeat') for i in range(len(assets)) if assets[i][0] in [a[0] for a in assets[:i]]]
    probs += [(i, 'title_long') for i, (t, _, _) in enumerate(assets) if len(t) > 70]
    probs += [(i, 'mismatched') for i, (_, s, f) in enumerate(assets) if (s, f) in MISMATCH]
    used = {s for _, s, _ in assets}
    gaps = sorted(set(STAGES) - used)
    by_stage = {s: sum(1 for _, ss, _ in assets if ss == s) for s in sorted(used)}
    return {'problems': sorted(probs), 'gaps': gaps, 'by_stage': by_stage, 'total': len(assets)}


DISCLAIMER = ('NOT_CLAIMED: this checks a supplied list against fixed tables. It does not say the content is '
              'valuable, that the mismatch table fits every funnel, or that coverage converts. No clinical or '
              'wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.content_marketing as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    good = [('A', 'awareness', 'blog'), ('B', 'consideration', 'guide'), ('C', 'decision', 'case_study')]
    assert ca(good) == {'problems': [], 'gaps': [], 'by_stage': dict((s, 1) for s in STAGES), 'total': 3}
    assert ca([]) == {'problems': [], 'gaps': list(STAGES), 'by_stage': {}, 'total': 0}
    assert ca([('A', 'awareness', 'blog'), ('A', 'decision', 'video')])['problems'] == [(1, 'repeat')]
    assert ca([('x' * 70, 'awareness', 'blog')])['problems'] == []
    assert ca([('x' * 71, 'awareness', 'blog')])['problems'] == [(0, 'title_long')]
    assert ca([('A', 'awareness', 'case_study')])['problems'] == [(0, 'mismatched')]
    assert ca([('A', 'decision', 'blog')])['problems'] == [(0, 'mismatched')]
    assert ca([('A', 'decision', 'guide')])['problems'] == []
    assert ca([('café launch', 'awareness', 'blog')])['problems'] == []
    r = ca([('A', 'awareness', 'case_study'), ('A', 'decision', 'blog')])
    assert r['problems'] == [(0, 'mismatched'), (1, 'mismatched'), (1, 'repeat')]
    assert r['gaps'] == ['consideration']


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4140 + part)
    seen, clean, gaps_hit = set(), 0, 0
    titles = ['A', 'B', 'C', 'café', '日本語', 'x' * 72, 'y']
    for _ in range(60):
        assets = []
        for _ in range(rnd.randint(0, 7)):
            assets.append((rnd.choice(titles), rnd.choice(STAGES), rnd.choice(FORMATS)))
        r = ca(assets)
        assert r == oracle(assets)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
        gaps_hit += bool(r['gaps'])
    assert len(seen) == 3 and clean >= 2 and gaps_hit > 10


def test_limits_accepted():
    assets = [('t%02d' % k, STAGES[k % 3], 'guide') for k in range(30)]
    r = ca(assets)
    assert r['problems'] == [] and r['gaps'] == [] and r['total'] == 30
    ca([('x' * 100, 'awareness', 'blog')])


def err(exc, msg, assets):
    with pytest.raises(exc) as e:
        ca(assets)
    assert str(e.value) == msg


SV = 'stage must be one of: awareness, consideration, decision'
FV = 'fmt must be one of: blog, case_study, guide, video, webinar'
TL = 'title length must be 1 to 100 characters'
NS = (None, 5, b'a', StrSub('a'))


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'assets must be an exact list', bad)
    err(V, 'asset count must be at most 30', [('t', 'awareness', 'blog')] * 31)
    for bad in (None, ['t', 'awareness', 'blog'], 'ab', TupleSub(('t', 'awareness', 'blog')), 5):
        err(T, 'each asset must be an exact tuple', [bad])
    for bad in ((), ('t', 'awareness'), ('t', 'awareness', 'blog', 1)):
        err(V, 'each asset must have 3 items', [bad])
    for bad in NS:
        err(T, 'title must be an exact string', [(bad, 'awareness', 'blog')])
    for bad in ('', 'x' * 101):
        err(V, TL, [(bad, 'awareness', 'blog')])
    for bad in NS:
        err(T, 'stage must be an exact string', [('t', bad, 'blog')])
    for bad in ('', 'Awareness', 'AWARENESS', 'é', 'ａ'):
        err(V, SV, [('t', bad, 'blog')])
    for bad in NS:
        err(T, 'fmt must be an exact string', [('t', 'awareness', bad)])
    for bad in ('', 'Blog', 'BLOG', 'é', 'ｂ'):
        err(V, FV, [('t', 'awareness', bad)])


def _order(err):
    err(T, 'assets must be an exact list', 'x')
    err(V, 'asset count must be at most 30', [None] * 31)
    err(T, 'each asset must be an exact tuple', [None, ('t',)])
    err(V, 'each asset must have 3 items', [('t',), None])
    err(T, 'title must be an exact string', [(5, 'x', 'x')])
    err(V, TL, [('', 5, 5)])
    err(T, 'stage must be an exact string', [('t', 5, 'x')])
    err(V, SV, [('t', 'Awareness', 'x')])
    err(T, 'fmt must be an exact string', [('t', 'awareness', 5)])
    err(V, FV, [('t', 'awareness', 'Blog')])
    err(T, 'title must be an exact string', [('t', 'awareness', 'blog'), (5, 'x', 'x')])
    err(T, 'stage must be an exact string', [('t', 'awareness', 'blog'), ('t', 5, 'x')])


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
