import random
import pytest
from sugarcode.extra_doc.public_relations import check_mentions as cm

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


SENTS = ('positive', 'neutral', 'negative')


def oracle(mentions):
    # written from the stated rule: fixed bars 10000/1000 on negative reach; same (source, sentiment) as earlier
    probs = [(i, 'crisis') for i, (_, s, r) in enumerate(mentions) if s == 'negative' and r >= 10000]
    probs += [(i, 'watch') for i, (_, s, r) in enumerate(mentions) if s == 'negative' and 1000 <= r < 10000]
    pairs = [(src, s) for src, s, _ in mentions]
    probs += [(i, 'repeat') for i in range(len(mentions)) if pairs[i] in pairs[:i]]
    net = sum(1 if s == 'positive' else -1 if s == 'negative' else 0 for _, s, _ in mentions)
    return {'problems': sorted(probs), 'net': net,
            'reach': sum(r for _, _, r in mentions), 'total': len(mentions)}


DISCLAIMER = ('NOT_CLAIMED: this sorts a supplied table against fixed bars. It does not say the reputation is good, '
              'that 10000 is the right crisis bar, or that any mention is real. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.public_relations as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert cm([]) == {'problems': [], 'net': 0, 'reach': 0, 'total': 0}
    assert cm([('blog', 'positive', 500)]) == {'problems': [], 'net': 1, 'reach': 500, 'total': 1}
    assert cm([('blog', 'negative', 9999)])['problems'] == [(0, 'watch')]
    assert cm([('blog', 'negative', 10000)])['problems'] == [(0, 'crisis')]
    assert cm([('blog', 'negative', 999)])['problems'] == []
    assert cm([('blog', 'negative', 1000)])['problems'] == [(0, 'watch')]
    assert cm([('blog', 'neutral', 1000000)])['problems'] == []
    assert cm([('blog', 'positive', 1000000)])['reach'] == 1000000
    assert cm([('a', 'positive', 1), ('b', 'negative', 1), ('c', 'neutral', 1)])['net'] == 0
    assert cm([('a', 'negative', 5), ('a', 'negative', 5)])['problems'] == [(1, 'repeat')]
    assert cm([('a', 'negative', 5), ('a', 'positive', 5)])['problems'] == []
    r = cm([('a', 'negative', 20000), ('a', 'negative', 2000)])
    assert r['problems'] == [(0, 'crisis'), (1, 'repeat'), (1, 'watch')] and r['net'] == -2


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4160 + part)
    seen, clean = set(), 0
    for _ in range(60):
        mentions = []
        for _ in range(rnd.randint(0, 7)):
            mentions.append((rnd.choice(('a', 'b', 'c')), rnd.choice(SENTS),
                             rnd.choice((0, 5, 999, 1000, 5000, 9999, 10000, 50000))))
        r = cm(mentions)
        assert r == oracle(mentions)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert len(seen) == 3 and clean >= 2


def test_limits_accepted():
    mentions = [('s%02d' % k, 'neutral', 1000000) for k in range(40)]
    r = cm(mentions)
    assert r['problems'] == [] and r['reach'] == 40000000 and r['total'] == 40
    cm([('a' * 24, 'positive', 0)])


def err(exc, msg, mentions):
    with pytest.raises(exc) as e:
        cm(mentions)
    assert str(e.value) == msg


SM = 'source must be 1 to 24 lowercase identifier characters'
SV = 'sentiment must be one of: negative, neutral, positive'
RR = 'reach must be between 0 and 1000000'
NS = (None, 5, b'a', StrSub('a'))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'mentions must be an exact list', bad)
    err(V, 'mention count must be at most 40', [('a', 'neutral', 0)] * 41)
    for bad in (None, ['a', 'neutral', 0], 'ab', TupleSub(('a', 'neutral', 0)), 5):
        err(T, 'each mention must be an exact tuple', [bad])
    for bad in ((), ('a', 'neutral'), ('a', 'neutral', 0, 1)):
        err(V, 'each mention must have 3 items', [bad])
    for bad in NS:
        err(T, 'source must be an exact string', [(bad, 'neutral', 0)])
    for bad in BAD:
        err(V, SM, [(bad, 'neutral', 0)])
    for bad in NS:
        err(T, 'sentiment must be an exact string', [('a', bad, 0)])
    for bad in ('', 'Negative', 'NEGATIVE', 'é', 'ｎ'):
        err(V, SV, [('a', bad, 0)])
    for bad in (None, 1.0, '1', True, False, IntSub(1), b'1'):
        err(T, 'reach must be an exact int', [('a', 'neutral', bad)])
    for bad in (-1, 1000001, 2 ** 40):
        err(V, RR, [('a', 'neutral', bad)])


def _order(err):
    err(T, 'mentions must be an exact list', 'x')
    err(V, 'mention count must be at most 40', [None] * 41)
    err(T, 'each mention must be an exact tuple', [None, ('a',)])
    err(V, 'each mention must have 3 items', [('a',), None])
    err(T, 'source must be an exact string', [(5, 'x', 'x')])
    err(V, SM, [('A', 'x', 'x')])
    err(T, 'sentiment must be an exact string', [('a', 5, 'x')])
    err(V, SV, [('a', 'Negative', 'x')])
    err(T, 'reach must be an exact int', [('a', 'neutral', 'x')])
    err(V, RR, [('a', 'neutral', -1)])
    err(T, 'source must be an exact string', [('a', 'neutral', 0), (5, 'x', 'x')])
    err(T, 'sentiment must be an exact string', [('a', 'neutral', 0), ('a', 5, 'x')])


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
