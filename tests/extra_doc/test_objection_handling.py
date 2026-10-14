import random
import pytest
from sugarcode.extra_doc.objection_handling import check_replies as cr

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(replies):
    # written from the stated rule: reply age over 240 is slow_reply; still open over 1440 is stale_open
    probs = []
    for i, (_, m, o) in enumerate(replies):
        if m > 240:
            probs.append((i, 'slow_reply'))
        if o == 'open' and m > 1440:
            probs.append((i, 'stale_open'))
    return {'problems': sorted(probs), 'objections': sorted({o for o, _, _ in replies}), 'total': len(replies)}


DISCLAIMER = ('NOT_CLAIMED: this checks a supplied reply list against two age bars. It does not say the concerns '
              'were addressed, that 240 or 1440 minutes are the right bars, or that any customer was satisfied. '
              'No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.objection_handling as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert cr([]) == {'problems': [], 'objections': [], 'total': 0}
    assert cr([('o', 0, 'open')]) == {'problems': [], 'objections': ['o'], 'total': 1}
    assert cr([('o', 240, 'resolved')])['problems'] == []
    assert cr([('o', 241, 'resolved')])['problems'] == [(0, 'slow_reply')]
    assert cr([('o', 10080, 'resolved')])['problems'] == [(0, 'slow_reply')]
    assert cr([('o', 1440, 'open')])['problems'] == [(0, 'slow_reply')]
    assert cr([('o', 1441, 'open')])['problems'] == [(0, 'slow_reply'), (0, 'stale_open')]
    assert cr([('o', 1441, 'deflected')])['problems'] == [(0, 'slow_reply')]
    assert cr([('o', 10080, 'open')])['problems'] == [(0, 'slow_reply'), (0, 'stale_open')]
    assert cr([('o', 100, 'open')])['problems'] == []
    assert cr([('a', 241, 'open'), ('b', 5000, 'open'), ('c', 10, 'resolved')])['problems'] == [
        (0, 'slow_reply'), (1, 'slow_reply'), (1, 'stale_open')]
    assert cr([('b', 1, 'open'), ('a', 1, 'open')]) == {'problems': [], 'objections': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4310 + part)
    seen, clean = set(), 0
    for _ in range(60):
        replies = []
        for _ in range(rnd.randint(0, 9)):
            replies.append((rnd.choice(('o1', 'o2', 'o3')),
                            rnd.choice((0, 240, 241, 1440, 1441, 10080, rnd.randint(0, 10080))),
                            rnd.choice(('resolved', 'deflected', 'open'))))
        r = cr(replies)
        assert r == oracle(replies)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'slow_reply', 'stale_open'} and clean >= 2


def test_limits_accepted():
    replies = [('o%02d' % k, 60, 'resolved') for k in range(40)]
    r = cr(replies)
    assert r['total'] == 40 and r['problems'] == []
    cr([('a' * 24, 10080, 'open')])
    cr([('a', 0, 'open')])


def err(exc, msg, replies):
    with pytest.raises(exc) as e:
        cr(replies)
    assert str(e.value) == msg


OM = 'objection must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'replies must be an exact list', bad)
    err(V, 'reply count must be at most 40', [('o', 0, 'open')] * 41)
    for bad in (None, ['o', 0, 'open'], 'ab', TupleSub(('o', 0, 'open')), 5):
        err(T, 'each reply must be an exact tuple', [bad])
    for bad in ((), ('o', 0), ('o', 0, 'open', 0)):
        err(V, 'each reply must have 3 items', [bad])
    for bad in NS:
        err(T, 'objection must be an exact string', [(bad, 0, 'open')])
        err(T, 'outcome must be an exact string', [('o', 0, bad)])
    for bad in BAD:
        err(V, OM, [(bad, 0, 'open')])
    for bad in NI:
        err(T, 'minutes must be an exact integer', [('o', bad, 'open')])
    for bad in (-1, 10081, -100, 10**9):
        err(V, 'minutes must be 0 to 10080', [('o', bad, 'open')])
    for bad in ('', 'Open', 'OPEN', 'open ', 'resolve', 'resolved\n', 'opén'):
        err(V, 'outcome must be resolved, deflected or open', [('o', 0, bad)])


def _order(err):
    err(T, 'replies must be an exact list', 'x')
    err(V, 'reply count must be at most 40', [None] * 41)
    err(T, 'each reply must be an exact tuple', [None, ('o',)])
    err(V, 'each reply must have 3 items', [('o',), None])
    err(T, 'objection must be an exact string', [(5, -1, 'x')])
    err(V, OM, [('A', -1, 'x')])
    err(T, 'minutes must be an exact integer', [('o', '0', 'x')])
    err(V, 'minutes must be 0 to 10080', [('o', -1, 'x')])
    err(T, 'outcome must be an exact string', [('o', 0, 5)])
    err(V, 'outcome must be resolved, deflected or open', [('o', 0, 'x')])
    err(T, 'objection must be an exact string', [('o', 0, 'open'), (5, 0, 'open')])
    err(T, 'minutes must be an exact integer', [('o', 0, 'open'), ('o', '0', 'open')])
    err(T, 'outcome must be an exact string', [('o', 0, 'open'), ('o', 0, 5)])


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
