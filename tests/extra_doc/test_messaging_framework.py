import random
import pytest
from sugarcode.extra_doc.messaging_framework import check_framework as cf

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(messages):
    # written from the stated rule: a rank/label/text "already used by an earlier message"
    ranks = [m[0] for m in messages]
    labels = [m[1] for m in messages]
    texts = [m[2] for m in messages]
    probs = [(i, 'rank_repeat') for i in range(len(messages)) if ranks[i] in ranks[:i]]
    probs += [(i, 'same_label') for i in range(len(messages)) if labels[i] in labels[:i]]
    probs += [(i, 'repeat') for i in range(len(messages)) if texts[i] in texts[:i]]
    probs += [(i, 'too_long') for i in range(len(messages)) if len(texts[i].split()) > 25]
    order = sorted(range(len(messages)), key=lambda i: (ranks[i], i))
    ordered = [labels[i] for i in order]
    return {'problems': sorted(probs), 'ordered': ordered, 'top': ordered[0] if len(ordered) else None}


DISCLAIMER = ('NOT_CLAIMED: this checks a supplied ranked list. It does not say the messages are persuasive, that '
              'the ranking is the right one, or that any audience read them. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.messaging_framework as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    good = [(1, 'value', 'We save you time'), (2, 'proof', 'Ten teams switched')]
    assert cf(good) == {'problems': [], 'ordered': ['value', 'proof'], 'top': 'value'}
    assert cf([]) == {'problems': [], 'ordered': [], 'top': None}
    assert cf([(3, 'b', 'x'), (1, 'a', 'y')])['ordered'] == ['a', 'b']
    assert cf([(1, 'a', 'x'), (1, 'b', 'y')])['problems'] == [(1, 'rank_repeat')]
    assert cf([(1, 'a', 'x'), (2, 'a', 'y')])['problems'] == [(1, 'same_label')]
    assert cf([(1, 'a', 'x'), (2, 'b', 'x')])['problems'] == [(1, 'repeat')]
    assert cf([(1, 'a', 'w ' * 24 + 'end')])['problems'] == []
    assert cf([(1, 'a', 'w ' * 25 + 'end')])['problems'] == [(0, 'too_long')]
    r = cf([(2, 'b', 'x'), (2, 'b', 'x')])
    assert r['problems'] == [(1, 'rank_repeat'), (1, 'repeat'), (1, 'same_label')]
    assert r['ordered'] == ['b', 'b']
    assert cf([(8, 'a', 'x')])['top'] == 'a'


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4050 + part)
    seen, clean = set(), 0
    for _ in range(60):
        msgs = []
        for _ in range(rnd.randint(0, 6)):
            r = rnd.randint(1, 5)
            l = rnd.choice('abcde')
            t = rnd.choice(('short text', 'hello there', 'w ' * rnd.randint(1, 30) + 'end'))
            msgs.append((r, l, t))
        r = cf(msgs)
        assert r == oracle(msgs)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert len(seen) == 4 and clean > 3


def test_limits_accepted():
    msgs = [(k, 'm%d' % k, 'text %d' % k) for k in range(1, 9)]
    assert cf(msgs) == {'problems': [], 'ordered': ['m%d' % k for k in range(1, 9)], 'top': 'm1'}
    cf([(8, 'a' * 24, 'x' * 120)])


def err(exc, msg, messages):
    with pytest.raises(exc) as e:
        cf(messages)
    assert str(e.value) == msg


LM = 'label must be 1 to 24 lowercase identifier characters'
TL = 'text length must be 1 to 120 characters'
NS = (None, 5, b'a', StrSub('a'))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'messages must be an exact list', bad)
    err(V, 'message count must be at most 8', [(1, 'a', 'x')] * 9)
    for bad in (None, [1, 'a', 'x'], 'ab', TupleSub((1, 'a', 'x')), 5):
        err(T, 'each message must be an exact tuple', [bad])
    for bad in ((), (1, 'a'), (1, 'a', 'x', 1)):
        err(V, 'each message must have 3 items', [bad])
    for bad in (None, 1.0, '1', True, False, IntSub(1), b'1'):
        err(T, 'rank must be an exact int', [(bad, 'a', 'x')])
    for bad in (0, 9, -1, 2 ** 40):
        err(V, 'rank must be between 1 and 8', [(bad, 'a', 'x')])
    for bad in NS:
        err(T, 'label must be an exact string', [(1, bad, 'x')])
    for bad in BAD:
        err(V, LM, [(1, bad, 'x')])
    for bad in NS:
        err(T, 'text must be an exact string', [(1, 'a', bad)])
    for bad in ('', 'x' * 121):
        err(V, TL, [(1, 'a', bad)])


def _order(err):
    err(T, 'messages must be an exact list', 'x')
    err(V, 'message count must be at most 8', [None] * 9)
    err(T, 'each message must be an exact tuple', [None, (1,)])
    err(V, 'each message must have 3 items', [(1,), None])
    err(T, 'rank must be an exact int', [('x', 5, 5)])
    err(V, 'rank must be between 1 and 8', [(0, 5, 5)])
    err(T, 'label must be an exact string', [(1, 5, 5)])
    err(V, LM, [(1, 'A', 5)])
    err(T, 'text must be an exact string', [(1, 'a', 5)])
    err(V, TL, [(1, 'a', '')])
    err(T, 'rank must be an exact int', [(1, 'a', 'x'), ('x', 0, 0)])
    err(T, 'label must be an exact string', [(1, 5, 5), ('x', 0, 0)])


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
