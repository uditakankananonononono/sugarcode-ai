import random
import pytest
from sugarcode.extra_doc.performance_management import check_reviews as ck

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(reviews):
    # written from the stated rule: rating under 2 is failing; under 1 improvement action is stagnant
    probs = []
    for i, (_, a, b) in enumerate(reviews):
        if a < 2:
            probs.append((i, 'failing'))
        if b < 1:
            probs.append((i, 'stagnant'))
    return {'problems': sorted(probs), 'employees': sorted({x for x, _, _ in reviews}), 'total': len(reviews)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied review numbers against two evaluation bars. It does not say '
              'performance improves, that 2 stars or 1 action are the right bars, or that any rating is fair. '
              'No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.performance_management as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'employees': [], 'total': 0}
    assert ck([('a', 2, 1)]) == {'problems': [], 'employees': ['a'], 'total': 1}
    assert ck([('a', 1, 1)])['problems'] == [(0, 'failing')]
    assert ck([('a', 0, 1)])['problems'] == [(0, 'failing')]
    assert ck([('a', 5, 1)])['problems'] == []
    assert ck([('a', 2, 0)])['problems'] == [(0, 'stagnant')]
    assert ck([('a', 1, 0)])['problems'] == [(0, 'failing'), (0, 'stagnant')]
    assert ck([('a', 1, 0), ('b', 3, 4), ('c', 5, 10)])['problems'] == [(0, 'failing'), (0, 'stagnant')]
    assert ck([('b', 3, 4), ('a', 3, 4)]) == {'problems': [], 'employees': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4940 + part)
    seen, clean = set(), 0
    for _ in range(60):
        reviews = []
        for _ in range(rnd.randint(0, 9)):
            reviews.append((rnd.choice(('x1', 'x2', 'x3')),
                            rnd.choice((0, 1, 2, 5, rnd.randint(0, 5))),
                            rnd.choice((0, 1, 10, rnd.randint(0, 10)))))
        r = ck(reviews)
        assert r == oracle(reviews)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'failing', 'stagnant'} and clean >= 2


def test_limits_accepted():
    reviews = [('x%02d' % k, 3, 4) for k in range(40)]
    r = ck(reviews)
    assert r['total'] == 40 and r['problems'] == []
    ck([('a' * 24, 5, 10)])
    ck([('a', 0, 0)])


def err(exc, msg, reviews):
    with pytest.raises(exc) as e:
        ck(reviews)
    assert str(e.value) == msg


NM = 'employee must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'reviews must be an exact list', bad)
    err(V, 'review count must be at most 40', [('x', 3, 4)] * 41)
    for bad in (None, ['x', 3, 4], 'ab', TupleSub(('x', 3, 4)), 5):
        err(T, 'each review must be an exact tuple', [bad])
    for bad in ((), ('x', 3), ('x', 3, 4, 0)):
        err(V, 'each review must have 3 items', [bad])
    for bad in NS:
        err(T, 'employee must be an exact string', [(bad, 3, 4)])
    for bad in BAD:
        err(V, NM, [(bad, 3, 4)])
    for bad in NI:
        err(T, 'rating must be an exact integer', [('x', bad, 4)])
        err(T, 'improvements must be an exact integer', [('x', 3, bad)])
    for bad in (-1, 6, -100, 10**9):
        err(V, 'rating must be 0 to 5', [('x', bad, 4)])
    for bad in (-1, 11, -100, 10**9):
        err(V, 'improvements must be 0 to 10', [('x', 3, bad)])


def _order(err):
    err(T, 'reviews must be an exact list', 'x')
    err(V, 'review count must be at most 40', [None] * 41)
    err(T, 'each review must be an exact tuple', [None, ('x',)])
    err(V, 'each review must have 3 items', [('x',), None])
    err(T, 'employee must be an exact string', [(5, -1, -1)])
    err(V, NM, [('A', -1, -1)])
    err(T, 'rating must be an exact integer', [('x', '0', -1)])
    err(V, 'rating must be 0 to 5', [('x', -1, -1)])
    err(T, 'improvements must be an exact integer', [('x', 0, '0')])
    err(V, 'improvements must be 0 to 10', [('x', 0, -1)])
    err(T, 'employee must be an exact string', [('x', 3, 4), (5, 3, 4)])
    err(T, 'rating must be an exact integer', [('x', 3, 4), ('x', '0', 4)])
    err(T, 'improvements must be an exact integer', [('x', 3, 4), ('x', 3, '0')])


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
