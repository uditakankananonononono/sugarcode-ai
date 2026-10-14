import random
import pytest
from sugarcode.extra_doc.media_relations import check_outreach as co

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


STAGE = {'pitched': 0, 'replied': 1, 'published': 2, 'declined': 2}
STATUSES = tuple(STAGE)


def oracle(entries):
    # written from the stated rule: stage drop below the running maximum; 3rd-or-later distinct outlet contact
    probs = []
    best = {}
    for i, (j, _, s) in enumerate(entries):
        if STAGE[s] < max([STAGE[ee[2]] for ee in entries[:i] if ee[0] == j] + [0]):
            probs.append((i, 'out_of_order'))
    for i, (j, o, _) in enumerate(entries):
        earlier = {ee[0] for ee in entries[:i] if ee[1] == o}
        if j not in earlier and len(earlier) >= 2:
            probs.append((i, 'blanketing'))
    pub = sorted({o for _, o, s in entries if s == 'published'})
    return {'problems': sorted(probs), 'published': pub, 'total': len(entries)}


DISCLAIMER = ('NOT_CLAIMED: this checks a supplied log against one stage order. It does not say the pitches were '
              'good, that three contacts is spam, or that any journalist replied. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.media_relations as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    good = [('j1', 'o1', 'pitched'), ('j1', 'o1', 'replied'), ('j1', 'o1', 'published')]
    assert co(good) == {'problems': [], 'published': ['o1'], 'total': 3}
    assert co([]) == {'problems': [], 'published': [], 'total': 0}
    assert co([('j1', 'o1', 'replied'), ('j1', 'o2', 'pitched')])['problems'] == [(1, 'out_of_order')]
    assert co([('j1', 'o1', 'published'), ('j1', 'o1', 'declined')])['problems'] == []
    assert co([('j1', 'o1', 'declined'), ('j1', 'o1', 'published')])['problems'] == []
    assert co([('j1', 'o1', 'published'), ('j1', 'o1', 'replied')])['problems'] == [(1, 'out_of_order')]
    three = [('j1', 'o1', 'pitched'), ('j2', 'o1', 'pitched'), ('j3', 'o1', 'pitched')]
    assert co(three)['problems'] == [(2, 'blanketing')]
    assert co(three[:2])['problems'] == []
    four = three + [('j4', 'o1', 'pitched')]
    assert co(four)['problems'] == [(2, 'blanketing'), (3, 'blanketing')]
    assert co([('j1', 'o1', 'pitched'), ('j2', 'o1', 'pitched'), ('j1', 'o1', 'replied')])['problems'] == []
    r = co([('j1', 'o1', 'replied'), ('j1', 'o1', 'pitched'), ('j1', 'o1', 'pitched')])
    assert r['problems'] == [(1, 'out_of_order'), (2, 'out_of_order')]
    assert co([('j1', 'o1', 'declined')])['published'] == []


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4170 + part)
    seen, clean = set(), 0
    for _ in range(60):
        entries = []
        for _ in range(rnd.randint(0, 9)):
            entries.append((rnd.choice(('j1', 'j2', 'j3', 'j4')), rnd.choice(('o1', 'o2')), rnd.choice(STATUSES)))
        r = co(entries)
        assert r == oracle(entries)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert len(seen) == 2 and clean >= 2


def test_limits_accepted():
    entries = [('j%02d' % k, 'o%d' % (k % 2), 'pitched') for k in range(40)]
    r = co(entries)
    expected = sorted([(k, 'blanketing') for k in range(4, 40, 2)] + [(k, 'blanketing') for k in range(5, 40, 2)])
    assert r['total'] == 40 and r['problems'] == expected
    co([('a' * 24, 'b' * 24, 'declined')])


def err(exc, msg, entries):
    with pytest.raises(exc) as e:
        co(entries)
    assert str(e.value) == msg


JM = 'journalist must be 1 to 24 lowercase identifier characters'
OM = 'outlet must be 1 to 24 lowercase identifier characters'
SV = 'status must be one of: declined, pitched, published, replied'
NS = (None, 5, b'a', StrSub('a'))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'entries must be an exact list', bad)
    err(V, 'entry count must be at most 40', [('j', 'o', 'pitched')] * 41)
    for bad in (None, ['j', 'o', 'pitched'], 'ab', TupleSub(('j', 'o', 'pitched')), 5):
        err(T, 'each entry must be an exact tuple', [bad])
    for bad in ((), ('j', 'o'), ('j', 'o', 'pitched', 1)):
        err(V, 'each entry must have 3 items', [bad])
    for bad in NS:
        err(T, 'journalist must be an exact string', [(bad, 'o', 'pitched')])
        err(T, 'outlet must be an exact string', [('j', bad, 'pitched')])
    for bad in BAD:
        err(V, JM, [(bad, 'o', 'pitched')])
        err(V, OM, [('j', bad, 'pitched')])
    for bad in NS:
        err(T, 'status must be an exact string', [('j', 'o', bad)])
    for bad in ('', 'Pitched', 'PITCHED', 'é', 'ｐ'):
        err(V, SV, [('j', 'o', bad)])


def _order(err):
    err(T, 'entries must be an exact list', 'x')
    err(V, 'entry count must be at most 40', [None] * 41)
    err(T, 'each entry must be an exact tuple', [None, ('j',)])
    err(V, 'each entry must have 3 items', [('j',), None])
    err(T, 'journalist must be an exact string', [(5, 'A', 5)])
    err(V, JM, [('A', 5, 5)])
    err(T, 'outlet must be an exact string', [('j', 5, 5)])
    err(V, OM, [('j', 'A', 5)])
    err(T, 'status must be an exact string', [('j', 'o', 5)])
    err(V, SV, [('j', 'o', 'Pitched')])
    err(T, 'journalist must be an exact string', [('j', 'o', 'pitched'), (5, 'o', 'pitched')])
    err(T, 'outlet must be an exact string', [('j', 'o', 'pitched'), ('j', 5, 'pitched')])


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
