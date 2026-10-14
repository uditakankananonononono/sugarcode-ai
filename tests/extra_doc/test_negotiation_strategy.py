import random
import pytest
from sugarcode.extra_doc.negotiation_strategy import check_plan as cp

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(items):
    # written from the stated rule: must concedes nothing; give concedes at least 20
    probs = []
    for i, (_, lv, c) in enumerate(items):
        if lv == 'must' and c > 0:
            probs.append((i, 'must_concedes'))
        if lv == 'give' and c < 20:
            probs.append((i, 'give_tight'))
    return {'problems': sorted(probs), 'items': sorted({it for it, _, _ in items}), 'total': len(items)}


DISCLAIMER = ('NOT_CLAIMED: this checks a supplied plan against two concession bars. It does not say the '
              'negotiation is planned well, that must-haves should never concede, or that any deal was reached. '
              'No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.negotiation_strategy as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert cp([]) == {'problems': [], 'items': [], 'total': 0}
    assert cp([('i', 'must', 0)]) == {'problems': [], 'items': ['i'], 'total': 1}
    assert cp([('i', 'must', 1)])['problems'] == [(0, 'must_concedes')]
    assert cp([('i', 'must', 100)])['problems'] == [(0, 'must_concedes')]
    assert cp([('i', 'want', 0)])['problems'] == []
    assert cp([('i', 'want', 100)])['problems'] == []
    assert cp([('i', 'want', 19)])['problems'] == []
    assert cp([('i', 'give', 20)])['problems'] == []
    assert cp([('i', 'give', 19)])['problems'] == [(0, 'give_tight')]
    assert cp([('i', 'give', 0)])['problems'] == [(0, 'give_tight')]
    assert cp([('i', 'give', 100)])['problems'] == []
    assert cp([('a', 'must', 5), ('b', 'give', 5), ('c', 'want', 5)])['problems'] == [
        (0, 'must_concedes'), (1, 'give_tight')]
    assert cp([('b', 'want', 1), ('a', 'want', 1)]) == {'problems': [], 'items': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4320 + part)
    seen, clean = set(), 0
    for _ in range(60):
        items = []
        for _ in range(rnd.randint(0, 9)):
            items.append((rnd.choice(('i1', 'i2', 'i3')), rnd.choice(('must', 'want', 'give')),
                          rnd.choice((0, 1, 19, 20, 21, 100, rnd.randint(0, 100)))))
        r = cp(items)
        assert r == oracle(items)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'must_concedes', 'give_tight'} and clean >= 2


def test_limits_accepted():
    items = [('i%02d' % k, 'want', k) for k in range(40)]
    r = cp(items)
    assert r['total'] == 40 and r['problems'] == []
    cp([('a' * 24, 'give', 100)])
    cp([('a', 'must', 0)])


def err(exc, msg, items):
    with pytest.raises(exc) as e:
        cp(items)
    assert str(e.value) == msg


IM = 'item must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'items must be an exact list', bad)
    err(V, 'item count must be at most 40', [('i', 'want', 0)] * 41)
    for bad in (None, ['i', 'want', 0], 'ab', TupleSub(('i', 'want', 0)), 5):
        err(T, 'each item must be an exact tuple', [bad])
    for bad in ((), ('i', 'want'), ('i', 'want', 0, 0)):
        err(V, 'each item must have 3 items', [bad])
    for bad in NS:
        err(T, 'item must be an exact string', [(bad, 'want', 0)])
        err(T, 'level must be an exact string', [('i', bad, 0)])
    for bad in BAD:
        err(V, IM, [(bad, 'want', 0)])
    for bad in ('', 'Must', 'MUST', 'must ', 'give0', 'want\n', 'müst'):
        err(V, 'level must be must, want or give', [('i', bad, 0)])
    for bad in NI:
        err(T, 'concession must be an exact integer', [('i', 'want', bad)])
    for bad in (-1, 101, -100, 10**9):
        err(V, 'concession must be 0 to 100', [('i', 'want', bad)])


def _order(err):
    err(T, 'items must be an exact list', 'x')
    err(V, 'item count must be at most 40', [None] * 41)
    err(T, 'each item must be an exact tuple', [None, ('i',)])
    err(V, 'each item must have 3 items', [('i',), None])
    err(T, 'item must be an exact string', [(5, 'x', -1)])
    err(V, IM, [('A', 'x', -1)])
    err(T, 'level must be an exact string', [('i', 5, -1)])
    err(V, 'level must be must, want or give', [('i', 'x', -1)])
    err(T, 'concession must be an exact integer', [('i', 'want', '0')])
    err(V, 'concession must be 0 to 100', [('i', 'want', -1)])
    err(T, 'item must be an exact string', [('i', 'want', 0), (5, 'want', 0)])
    err(T, 'level must be an exact string', [('i', 'want', 0), ('i', 5, 0)])
    err(T, 'concession must be an exact integer', [('i', 'want', 0), ('i', 'want', '0')])


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
