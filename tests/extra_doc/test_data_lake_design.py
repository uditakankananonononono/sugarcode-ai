import random
import pytest
from sugarcode.extra_doc.data_lake_design import check_datasets as ck

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
    # written from the stated rule: over 50000 gb is sprawling; under 2 zones is unzoned
    probs = []
    for i, (_, a, b) in enumerate(items):
        if a > 50000:
            probs.append((i, 'sprawling'))
        if b < 2:
            probs.append((i, 'unzoned'))
    return {'problems': sorted(probs), 'datasets': sorted({x for x, _, _ in items}), 'total': len(items)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied storage numbers against two raw-data bars. It does not say raw data is stored well, that 50000 gb or 2 zones are the right bars, or that any byte is safe. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.data_lake_design as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'datasets': [], 'total': 0}
    assert ck([('a', 1000, 3)]) == {'problems': [], 'datasets': ['a'], 'total': 1}
    assert ck([('a', 50001, 3)])['problems'] == [(0, 'sprawling')]
    assert ck([('a', 100000, 3)])['problems'] == [(0, 'sprawling')]
    assert ck([('a', 1000, 1)])['problems'] == [(0, 'unzoned')]
    assert ck([('a', 1000, 0)])['problems'] == [(0, 'unzoned')]
    assert ck([('a', 50001, 1)])['problems'] == [((0, 'sprawling')), ((0, 'unzoned'))]
    assert ck([('a', 50001, 1), ('b', 1000, 3), ('c', 100000, 3)])['problems'] == [
        (0, 'sprawling'), (0, 'unzoned'), (2, 'sprawling')]
    assert ck([('b', 1000, 3), ('a', 1000, 3)]) == {'problems': [], 'datasets': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(5370 + part)
    seen, clean = set(), 0
    for _ in range(60):
        items = []
        for _ in range(rnd.randint(0, 9)):
            items.append((rnd.choice(('x1', 'x2', 'x3')),
                          rnd.choice((0, 50000, 50001, 100000, rnd.randint(0, 100000))),
                          rnd.choice((0, 1, 2, 10, rnd.randint(0, 10)))))
        r = ck(items)
        assert r == oracle(items)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'sprawling', 'unzoned'} and clean >= 2


def test_limits_accepted():
    items = [('x%02d' % k, 1000, 3) for k in range(40)]
    r = ck(items)
    assert r['total'] == 40 and r['problems'] == []
    ck([('a' * 24, 100000, 10)])
    ck([('a', 0, 0)])


def err(exc, msg, items):
    with pytest.raises(exc) as e:
        ck(items)
    assert str(e.value) == msg


NM = 'dataset must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'datasets must be an exact list', bad)
    err(V, 'dataset count must be at most 40', [('x', 1000, 3)] * 41)
    for bad in (None, ['x', 1000, 3], 'ab', TupleSub(('x', 1000, 3)), 5):
        err(T, 'each dataset must be an exact tuple', [bad])
    for bad in ((), ('x', 1000), ('x', 1000, 3, 0)):
        err(V, 'each dataset must have 3 items', [bad])
    for bad in NS:
        err(T, 'dataset must be an exact string', [(bad, 1000, 3)])
    for bad in BAD:
        err(V, NM, [(bad, 1000, 3)])
    for bad in NI:
        err(T, 'gb' + ' must be an exact integer', [('x', bad, 3)])
        err(T, 'zones' + ' must be an exact integer', [('x', 1000, bad)])
    for bad in (-1, 100001, -100, 10**9):
        err(V, 'gb' + ' must be 0 to 100000', [('x', bad, 3)])
    for bad in (-1, 11, -100, 10**9):
        err(V, 'zones' + ' must be 0 to 10', [('x', 1000, bad)])


def _order(err):
    err(T, 'datasets must be an exact list', 'x')
    err(V, 'dataset count must be at most 40', [None] * 41)
    err(T, 'each dataset must be an exact tuple', [None, ('x',)])
    err(V, 'each dataset must have 3 items', [('x',), None])
    err(T, 'dataset must be an exact string', [(5, -1, -1)])
    err(V, NM, [('A', -1, -1)])
    err(T, 'gb' + ' must be an exact integer', [('x', '0', -1)])
    err(V, 'gb' + ' must be 0 to 100000', [('x', -1, -1)])
    err(T, 'zones' + ' must be an exact integer', [('x', 0, '0')])
    err(V, 'zones' + ' must be 0 to 10', [('x', 0, -1)])
    err(T, 'dataset must be an exact string', [('x', 1000, 3), (5, 1000, 3)])
    err(T, 'gb' + ' must be an exact integer', [('x', 1000, 3), ('x', '0', 3)])
    err(T, 'zones' + ' must be an exact integer', [('x', 1000, 3), ('x', 1000, '0')])


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
