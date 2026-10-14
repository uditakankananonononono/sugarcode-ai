import random
import pytest
from sugarcode.extra_doc.semantic_search import check_indexes as ck

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
    # written from the stated rule: under 1000 embeddings is underindexed; under 64 dims is low dim
    probs = []
    for i, (_, a, b) in enumerate(items):
        if a < 1000:
            probs.append((i, 'underindexed'))
        if b < 64:
            probs.append((i, 'low_dim'))
    return {'problems': sorted(probs), 'indexes': sorted({x for x, _, _ in items}), 'total': len(items)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied index numbers against two meaning bars. It does not say results match meaning, that 1000 embeddings or 64 dims are the right bars, or that any search succeeds. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.semantic_search as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'indexes': [], 'total': 0}
    assert ck([('a', 5000, 256)]) == {'problems': [], 'indexes': ['a'], 'total': 1}
    assert ck([('a', 999, 256)])['problems'] == [(0, 'underindexed')]
    assert ck([('a', 0, 256)])['problems'] == [(0, 'underindexed')]
    assert ck([('a', 5000, 63)])['problems'] == [(0, 'low_dim')]
    assert ck([('a', 5000, 0)])['problems'] == [(0, 'low_dim')]
    assert ck([('a', 999, 63)])['problems'] == [((0, 'low_dim')), ((0, 'underindexed'))]
    assert ck([('a', 999, 63), ('b', 5000, 256), ('c', 0, 256)])['problems'] == [
        (0, 'low_dim'), (0, 'underindexed'), (2, 'underindexed')]
    assert ck([('b', 5000, 256), ('a', 5000, 256)]) == {'problems': [], 'indexes': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(5680 + part)
    seen, clean = set(), 0
    for _ in range(60):
        items = []
        for _ in range(rnd.randint(0, 9)):
            items.append((rnd.choice(('x1', 'x2', 'x3')),
                          rnd.choice((0, 999, 1000, 1000000, rnd.randint(0, 1000000))),
                          rnd.choice((0, 63, 64, 4096, rnd.randint(0, 4096)))))
        r = ck(items)
        assert r == oracle(items)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'underindexed', 'low_dim'} and clean >= 2


def test_limits_accepted():
    items = [('x%02d' % k, 5000, 256) for k in range(40)]
    r = ck(items)
    assert r['total'] == 40 and r['problems'] == []
    ck([('a' * 24, 1000000, 4096)])
    ck([('a', 0, 0)])


def err(exc, msg, items):
    with pytest.raises(exc) as e:
        ck(items)
    assert str(e.value) == msg


NM = 'index must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'indexes must be an exact list', bad)
    err(V, 'index count must be at most 40', [('x', 5000, 256)] * 41)
    for bad in (None, ['x', 5000, 256], 'ab', TupleSub(('x', 5000, 256)), 5):
        err(T, 'each index must be an exact tuple', [bad])
    for bad in ((), ('x', 5000), ('x', 5000, 256, 0)):
        err(V, 'each index must have 3 items', [bad])
    for bad in NS:
        err(T, 'index must be an exact string', [(bad, 5000, 256)])
    for bad in BAD:
        err(V, NM, [(bad, 5000, 256)])
    for bad in NI:
        err(T, 'embeddings' + ' must be an exact integer', [('x', bad, 256)])
        err(T, 'dims' + ' must be an exact integer', [('x', 5000, bad)])
    for bad in (-1, 1000001, -100, 10**9):
        err(V, 'embeddings' + ' must be 0 to 1000000', [('x', bad, 256)])
    for bad in (-1, 4097, -100, 10**9):
        err(V, 'dims' + ' must be 0 to 4096', [('x', 5000, bad)])


def _order(err):
    err(T, 'indexes must be an exact list', 'x')
    err(V, 'index count must be at most 40', [None] * 41)
    err(T, 'each index must be an exact tuple', [None, ('x',)])
    err(V, 'each index must have 3 items', [('x',), None])
    err(T, 'index must be an exact string', [(5, -1, -1)])
    err(V, NM, [('A', -1, -1)])
    err(T, 'embeddings' + ' must be an exact integer', [('x', '0', -1)])
    err(V, 'embeddings' + ' must be 0 to 1000000', [('x', -1, -1)])
    err(T, 'dims' + ' must be an exact integer', [('x', 0, '0')])
    err(V, 'dims' + ' must be 0 to 4096', [('x', 0, -1)])
    err(T, 'index must be an exact string', [('x', 5000, 256), (5, 5000, 256)])
    err(T, 'embeddings' + ' must be an exact integer', [('x', 5000, 256), ('x', '0', 256)])
    err(T, 'dims' + ' must be an exact integer', [('x', 5000, 256), ('x', 5000, '0')])


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
