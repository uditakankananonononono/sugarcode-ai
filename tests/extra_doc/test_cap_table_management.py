import random
import pytest
from sugarcode.extra_doc.cap_table_management import check_holders as ck

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(holders):
    # written from the stated rule: over 500000 shares is concentrated; under 1 grant is untracked
    probs = []
    for i, (_, a, b) in enumerate(holders):
        if a > 500000:
            probs.append((i, 'concentrated'))
        if b < 1:
            probs.append((i, 'untracked'))
    return {'problems': sorted(probs), 'holders': sorted({x for x, _, _ in holders}), 'total': len(holders)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied holding numbers against two tracking bars. It does not say '
              'ownership is tracked correctly, that 500000 shares or 1 grant are the right bars, or that the '
              'cap table balances. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.cap_table_management as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'holders': [], 'total': 0}
    assert ck([('a', 500000, 1)]) == {'problems': [], 'holders': ['a'], 'total': 1}
    assert ck([('a', 500001, 1)])['problems'] == [(0, 'concentrated')]
    assert ck([('a', 1000000, 1)])['problems'] == [(0, 'concentrated')]
    assert ck([('a', 0, 1)])['problems'] == []
    assert ck([('a', 500000, 0)])['problems'] == [(0, 'untracked')]
    assert ck([('a', 500001, 0)])['problems'] == [(0, 'concentrated'), (0, 'untracked')]
    assert ck([('a', 500001, 0), ('b', 100, 5), ('c', 1000000, 100)])['problems'] == [
        (0, 'concentrated'), (0, 'untracked'), (2, 'concentrated')]
    assert ck([('b', 100, 5), ('a', 100, 5)]) == {'problems': [], 'holders': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4970 + part)
    seen, clean = set(), 0
    for _ in range(60):
        holders = []
        for _ in range(rnd.randint(0, 9)):
            holders.append((rnd.choice(('x1', 'x2', 'x3')),
                            rnd.choice((0, 500000, 500001, 1000000, rnd.randint(0, 1000000))),
                            rnd.choice((0, 1, 100, rnd.randint(0, 100)))))
        r = ck(holders)
        assert r == oracle(holders)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'concentrated', 'untracked'} and clean >= 2


def test_limits_accepted():
    holders = [('x%02d' % k, 100, 5) for k in range(40)]
    r = ck(holders)
    assert r['total'] == 40 and r['problems'] == []
    ck([('a' * 24, 1000000, 100)])
    ck([('a', 0, 0)])


def err(exc, msg, holders):
    with pytest.raises(exc) as e:
        ck(holders)
    assert str(e.value) == msg


NM = 'holder must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'holders must be an exact list', bad)
    err(V, 'holder count must be at most 40', [('x', 100, 5)] * 41)
    for bad in (None, ['x', 100, 5], 'ab', TupleSub(('x', 100, 5)), 5):
        err(T, 'each holder must be an exact tuple', [bad])
    for bad in ((), ('x', 100), ('x', 100, 5, 0)):
        err(V, 'each holder must have 3 items', [bad])
    for bad in NS:
        err(T, 'holder must be an exact string', [(bad, 100, 5)])
    for bad in BAD:
        err(V, NM, [(bad, 100, 5)])
    for bad in NI:
        err(T, 'shares must be an exact integer', [('x', bad, 5)])
        err(T, 'grants must be an exact integer', [('x', 100, bad)])
    for bad in (-1, 1000001, -100, 10**9):
        err(V, 'shares must be 0 to 1000000', [('x', bad, 5)])
    for bad in (-1, 101, -100, 10**9):
        err(V, 'grants must be 0 to 100', [('x', 100, bad)])


def _order(err):
    err(T, 'holders must be an exact list', 'x')
    err(V, 'holder count must be at most 40', [None] * 41)
    err(T, 'each holder must be an exact tuple', [None, ('x',)])
    err(V, 'each holder must have 3 items', [('x',), None])
    err(T, 'holder must be an exact string', [(5, -1, -1)])
    err(V, NM, [('A', -1, -1)])
    err(T, 'shares must be an exact integer', [('x', '0', -1)])
    err(V, 'shares must be 0 to 1000000', [('x', -1, -1)])
    err(T, 'grants must be an exact integer', [('x', 0, '0')])
    err(V, 'grants must be 0 to 100', [('x', 0, -1)])
    err(T, 'holder must be an exact string', [('x', 100, 5), (5, 100, 5)])
    err(T, 'shares must be an exact integer', [('x', 100, 5), ('x', '0', 5)])
    err(T, 'grants must be an exact integer', [('x', 100, 5), ('x', 100, '0')])


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
