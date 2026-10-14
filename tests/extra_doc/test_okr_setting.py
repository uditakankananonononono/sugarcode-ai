import random
import pytest
from sugarcode.extra_doc.okr_setting import check_okrs as ck

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(okrs):
    # written from the stated rule: over 5 objectives is top heavy; under 1 key result is unmeasured
    probs = []
    for i, (_, a, b) in enumerate(okrs):
        if a > 5:
            probs.append((i, 'top_heavy'))
        if b < 1:
            probs.append((i, 'unmeasured'))
    return {'problems': sorted(probs), 'okrs': sorted({x for x, _, _ in okrs}), 'total': len(okrs)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied okr numbers against two definition bars. It does not say '
              'objectives or key results are defined, that 5 objectives or 1 result are the right bars, or '
              'that anything is achieved. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.okr_setting as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'okrs': [], 'total': 0}
    assert ck([('a', 5, 1)]) == {'problems': [], 'okrs': ['a'], 'total': 1}
    assert ck([('a', 6, 1)])['problems'] == [(0, 'top_heavy')]
    assert ck([('a', 10, 1)])['problems'] == [(0, 'top_heavy')]
    assert ck([('a', 0, 1)])['problems'] == []
    assert ck([('a', 5, 0)])['problems'] == [(0, 'unmeasured')]
    assert ck([('a', 6, 0)])['problems'] == [(0, 'top_heavy'), (0, 'unmeasured')]
    assert ck([('a', 6, 0), ('b', 3, 4), ('c', 10, 30)])['problems'] == [
        (0, 'top_heavy'), (0, 'unmeasured'), (2, 'top_heavy')]
    assert ck([('b', 3, 4), ('a', 3, 4)]) == {'problems': [], 'okrs': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4910 + part)
    seen, clean = set(), 0
    for _ in range(60):
        okrs = []
        for _ in range(rnd.randint(0, 9)):
            okrs.append((rnd.choice(('x1', 'x2', 'x3')),
                         rnd.choice((0, 5, 6, 10, rnd.randint(0, 10))),
                         rnd.choice((0, 1, 30, rnd.randint(0, 30)))))
        r = ck(okrs)
        assert r == oracle(okrs)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'top_heavy', 'unmeasured'} and clean >= 2


def test_limits_accepted():
    okrs = [('x%02d' % k, 3, 4) for k in range(40)]
    r = ck(okrs)
    assert r['total'] == 40 and r['problems'] == []
    ck([('a' * 24, 10, 30)])
    ck([('a', 0, 0)])


def err(exc, msg, okrs):
    with pytest.raises(exc) as e:
        ck(okrs)
    assert str(e.value) == msg


NM = 'okr must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'okrs must be an exact list', bad)
    err(V, 'okr count must be at most 40', [('x', 3, 4)] * 41)
    for bad in (None, ['x', 3, 4], 'ab', TupleSub(('x', 3, 4)), 5):
        err(T, 'each okr must be an exact tuple', [bad])
    for bad in ((), ('x', 3), ('x', 3, 4, 0)):
        err(V, 'each okr must have 3 items', [bad])
    for bad in NS:
        err(T, 'okr must be an exact string', [(bad, 3, 4)])
    for bad in BAD:
        err(V, NM, [(bad, 3, 4)])
    for bad in NI:
        err(T, 'objectives must be an exact integer', [('x', bad, 4)])
        err(T, 'key_results must be an exact integer', [('x', 3, bad)])
    for bad in (-1, 11, -100, 10**9):
        err(V, 'objectives must be 0 to 10', [('x', bad, 4)])
    for bad in (-1, 31, -100, 10**9):
        err(V, 'key_results must be 0 to 30', [('x', 3, bad)])


def _order(err):
    err(T, 'okrs must be an exact list', 'x')
    err(V, 'okr count must be at most 40', [None] * 41)
    err(T, 'each okr must be an exact tuple', [None, ('x',)])
    err(V, 'each okr must have 3 items', [('x',), None])
    err(T, 'okr must be an exact string', [(5, -1, -1)])
    err(V, NM, [('A', -1, -1)])
    err(T, 'objectives must be an exact integer', [('x', '0', -1)])
    err(V, 'objectives must be 0 to 10', [('x', -1, -1)])
    err(T, 'key_results must be an exact integer', [('x', 0, '0')])
    err(V, 'key_results must be 0 to 30', [('x', 0, -1)])
    err(T, 'okr must be an exact string', [('x', 3, 4), (5, 3, 4)])
    err(T, 'objectives must be an exact integer', [('x', 3, 4), ('x', '0', 4)])
    err(T, 'key_results must be an exact integer', [('x', 3, 4), ('x', 3, '0')])


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
