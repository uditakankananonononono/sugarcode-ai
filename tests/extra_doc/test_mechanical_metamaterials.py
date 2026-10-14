import random
import pytest
from sugarcode.extra_doc.mechanical_metamaterials import check_lattices as ck

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
    # written from the stated rule: under 100 unit cells is coarse; under 1 gradient is uniform only
    probs = []
    for i, (_, a, b) in enumerate(items):
        if a < 100:
            probs.append((i, 'coarse'))
        if b < 1:
            probs.append((i, 'uniform_only'))
    return {'problems': sorted(probs), 'lattices': sorted({x for x, _, _ in items}), 'total': len(items)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied lattice numbers against two structure bars. It does not say any property emerges, that 100 cells or 1 gradient are the right bars, or that any lattice bears load. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.mechanical_metamaterials as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'lattices': [], 'total': 0}
    assert ck([('a', 500, 2)]) == {'problems': [], 'lattices': ['a'], 'total': 1}
    assert ck([('a', 99, 2)])['problems'] == [(0, 'coarse')]
    assert ck([('a', 0, 2)])['problems'] == [(0, 'coarse')]
    assert ck([('a', 500, 0)])['problems'] == [(0, 'uniform_only')]
    assert ck([('a', 500, 0)])['problems'] == [(0, 'uniform_only')]
    assert ck([('a', 99, 0)])['problems'] == [(0, 'coarse'), (0, 'uniform_only')]
    assert ck([('a', 99, 0), ('b', 500, 2), ('c', 0, 2)])['problems'] == [
        (0, 'coarse'), (0, 'uniform_only'), (2, 'coarse')]
    assert ck([('b', 500, 2), ('a', 500, 2)]) == {'problems': [], 'lattices': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(9580 + part)
    seen, clean = set(), 0
    for _ in range(60):
        items = []
        for _ in range(rnd.randint(0, 9)):
            items.append((rnd.choice(('x1', 'x2', 'x3')),
                          rnd.choice((0, 99, 100, 1000000, rnd.randint(0, 1000000))),
                          rnd.choice((0, 1, 100, rnd.randint(0, 100)))))
        r = ck(items)
        assert r == oracle(items)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'coarse', 'uniform_only'} and clean >= 2


def test_limits_accepted():
    items = [('x%02d' % k, 500, 2) for k in range(40)]
    r = ck(items)
    assert r['total'] == 40 and r['problems'] == []
    ck([('a' * 24, 1000000, 100)])
    ck([('a', 0, 0)])


def err(exc, msg, items):
    with pytest.raises(exc) as e:
        ck(items)
    assert str(e.value) == msg


NM = 'lattice must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')
PL = 'lattices must be an exact list'
CNT = 'lattice count must be at most 40'
TUP = 'each lattice must be an exact tuple'
IT3 = 'each lattice must have 3 items'
NSS = 'lattice must be an exact string'
FA = 'unit_cells'
FB = 'gradients'


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, PL, bad)
    err(V, CNT, [('x', 500, 2)] * 41)
    for bad in (None, ['x', 500, 2], 'ab', TupleSub(('x', 500, 2)), 5):
        err(T, TUP, [bad])
    for bad in ((), ('x', 500), ('x', 500, 2, 0)):
        err(V, IT3, [bad])
    for bad in NS:
        err(T, NSS, [(bad, 500, 2)])
    for bad in BAD:
        err(V, NM, [(bad, 500, 2)])
    for bad in NI:
        err(T, FA + ' must be an exact integer', [('x', bad, 2)])
        err(T, FB + ' must be an exact integer', [('x', 500, bad)])
    for bad in (-1, 1000001, -100, 10**9):
        err(V, FA + ' must be 0 to 1000000', [('x', bad, 2)])
    for bad in (-1, 101, -100, 10**9):
        err(V, FB + ' must be 0 to 100', [('x', 500, bad)])


def _order(err):
    err(T, PL, 'x')
    err(V, CNT, [None] * 41)
    err(T, TUP, [None, ('x',)])
    err(V, IT3, [('x',), None])
    err(T, NSS, [(5, -1, -1)])
    err(V, NM, [('A', -1, -1)])
    err(T, FA + ' must be an exact integer', [('x', '0', -1)])
    err(V, FA + ' must be 0 to 1000000', [('x', -1, -1)])
    err(T, FB + ' must be an exact integer', [('x', 0, '0')])
    err(V, FB + ' must be 0 to 100', [('x', 0, -1)])
    err(T, NSS, [('x', 500, 2), (5, 500, 2)])
    err(T, FA + ' must be an exact integer', [('x', 500, 2), ('x', '0', 2)])
    err(T, FB + ' must be an exact integer', [('x', 500, 2), ('x', 500, '0')])


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


def test_name_underscore_accepted():
    assert ck([('a_b', 500, 2)]) == {'problems': [], 'lattices': ['a_b'], 'total': 1}


def test_name_interior_space_rejected():
    err(V, NM, [('a b', 500, 2)])
