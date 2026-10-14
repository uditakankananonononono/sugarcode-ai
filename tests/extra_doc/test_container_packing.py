import itertools
import random
import pytest
from sugarcode.extra_doc.container_packing import place_containers as pc

T, V = TypeError, ValueError


class StrSub(str):
    pass


class IntSub(int):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


def oracle(nodes, containers):
    # explicit per-node lists; free space is recomputed from what a node holds each time
    held = {n: [] for n, _, _ in nodes}
    cap = {n: (c, m) for n, c, m in nodes}
    order = sorted(containers, key=lambda c: (-c[1], -c[2], c[0]))
    left = []
    for name, cpu, mem in order:
        target = None
        for node in sorted(cap):
            free_c = cap[node][0] - sum(x[1] for x in held[node])
            free_m = cap[node][1] - sum(x[2] for x in held[node])
            if cpu <= free_c and mem <= free_m:
                target = node
                break
        if target is None:
            left.append(name)
        else:
            held[target].append((name, cpu, mem))
    placed = sorted((x[0], n) for n in held for x in held[n])
    usage = [(n, sum(x[1] for x in held[n]), sum(x[2] for x in held[n])) for n in sorted(cap)]
    return {'placements': placed, 'unplaced': sorted(left), 'usage': usage}


def test_hand_cases():
    r = pc([('n1', 10, 10), ('n2', 10, 10)], [('a', 6, 1), ('b', 5, 1), ('c', 5, 1), ('d', 4, 1)])
    # order a(6), b(5), c(5), d(4): a on n1; b: n1 has 4 free so n2; c: n1 4 free, n2 5 free -> n2; d: n1 4 free -> n1
    assert r == {'placements': [('a', 'n1'), ('b', 'n2'), ('c', 'n2'), ('d', 'n1')], 'unplaced': [],
                 'usage': [('n1', 10, 2), ('n2', 10, 2)]}
    assert pc([('n', 5, 5)], []) == {'placements': [], 'unplaced': [], 'usage': [('n', 0, 0)]}
    r = pc([('n', 5, 5)], [('big', 6, 1), ('ok', 5, 5), ('small', 1, 1)])
    assert r == {'placements': [('ok', 'n')], 'unplaced': ['big', 'small'], 'usage': [('n', 5, 5)]}
    # memory can be the limit even when cpu fits
    assert pc([('n', 100, 4)], [('a', 1, 5)])['unplaced'] == ['a']
    assert pc([('n', 100, 5)], [('a', 1, 5)])['unplaced'] == []
    assert pc([('n', 5, 100)], [('a', 6, 1)])['unplaced'] == ['a']
    # a container that fits nowhere does not stop smaller ones being tried
    r = pc([('n', 10, 10)], [('huge', 11, 1), ('tiny', 1, 1)])
    assert r['placements'] == [('tiny', 'n')] and r['unplaced'] == ['huge']
    # ties: larger mem first, then name
    r = pc([('n', 10, 10)], [('b', 5, 5), ('a', 5, 5), ('c', 5, 6)])
    assert r == {'placements': [('c', 'n')], 'unplaced': ['a', 'b'], 'usage': [('n', 5, 6)]}


def test_tie_order_exact():
    # only one slot: the first container in (cpu desc, mem desc, name) order gets it
    assert pc([('n', 5, 10)], [('b', 5, 5), ('a', 5, 5)])['placements'] == [('a', 'n')]
    assert pc([('n', 5, 10)], [('a', 5, 5), ('z', 5, 6)])['placements'] == [('z', 'n')]
    assert pc([('n', 5, 10)], [('a', 4, 9), ('z', 5, 1)])['placements'] == [('z', 'n')]
    # nodes are tried in name order, not list order
    assert pc([('b', 9, 9), ('a', 9, 9)], [('x', 1, 1)])['placements'] == [('x', 'a')]


def test_random_vs_oracle_and_invariants():
    rnd = random.Random(614)
    unplaced_seen = placed_all = 0
    for _ in range(500):
        nodes = [('n%d' % i, rnd.randint(1, 12), rnd.randint(1, 12)) for i in range(rnd.randint(1, 4))]
        conts = [('c%02d' % i, rnd.randint(1, 8), rnd.randint(1, 8)) for i in range(rnd.randint(0, 9))]
        rnd.shuffle(nodes)
        rnd.shuffle(conts)
        r = pc(nodes, conts)
        assert r == oracle(nodes, conts)
        cap = {n: (c, m) for n, c, m in nodes}
        size = {n: (c, m) for n, c, m in conts}
        for node, cu, mu in r['usage']:                                         # never over capacity
            assert cu <= cap[node][0] and mu <= cap[node][1]
        assert sorted([x[0] for x in r['placements']] + r['unplaced']) == sorted(size)
        for name in r['unplaced']:                                              # free space only shrinks, so it fits nowhere
            for node, cu, mu in r['usage']:
                assert size[name][0] > cap[node][0] - cu or size[name][1] > cap[node][1] - mu
        unplaced_seen += bool(r['unplaced'])
        placed_all += not r['unplaced']
    assert unplaced_seen > 80 and placed_all > 80
    n, c = [('a', 5, 5)], [('x', 1, 1)]
    pc(n, c)
    assert n == [('a', 5, 5)] and c == [('x', 1, 1)]


def test_edges_accepted():
    nodes = [('n%02d' % i, 1000000, 1000000) for i in range(16)]
    assert len(pc(nodes, [])['usage']) == 16
    conts = [('c%02d' % i, 1, 1) for i in range(64)]
    r = pc(nodes[:1], conts)
    assert len(r['placements']) == 64 and r['usage'] == [('n00', 64, 64)]
    r = pc([('n', 1000000, 1000000)], [('a', 1000000, 1000000), ('b', 1, 1)])
    assert r['unplaced'] == ['b']
    pc([('a' * 24, 1, 1)], [('b' * 24, 1, 1)])


def err(exc, msg, nodes, conts):
    with pytest.raises(exc) as e:
        pc(nodes, conts)
    assert str(e.value) == msg


def test_pins_every_slot_for_both_lists():
    ok = ('a', 1, 1)
    for which, rng in (('nodes', '1 and 16'), ('containers', '0 and 64')):
        def e(exc, msg, rows, which=which):
            err(exc, which + ': ' + msg, *((rows, [ok]) if which == 'nodes' else ([ok], rows)))
        for bad in (None, (), 'x', {1}, 5):
            e(T, 'must be an exact list', bad)
        e(T, 'must be an exact list', ListSub([ok]))
        if which == 'nodes':
            e(V, 'count must be between 1 and 16', [])
        e(V, 'count must be between ' + rng, [('n%02d' % i, 1, 1) for i in range(17 if which == 'nodes' else 65)])
        for bad in (None, [], 'abc', TupleSub(ok), 5):
            e(T, 'row must be an exact tuple', [bad])
        for bad_row in ((), ('a',), ('a', 1), ('a', 1, 1, 1)):
            e(V, 'row must have 3 items', [bad_row])
        for bad in (None, 5, b'a', StrSub('a')):
            e(T, 'name must be an exact string', [(bad, 1, 1)])
        for bad in ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a'):
            e(V, 'name must be 1 to 24 lowercase identifier characters', [(bad, 1, 1)])
        for slot, label in ((1, 'cpu'), (2, 'mem')):
            for bad in (True, False, 1.0, '1', None, IntSub(1), [1]):
                row = list(ok)
                row[slot] = bad
                e(T, label + ' must be a nonbool int', [tuple(row)])
            for bad in (0, -1, 1000001):
                row = list(ok)
                row[slot] = bad
                e(V, label + ' must be between 1 and 1000000', [tuple(row)])
        e(V, 'duplicate name', [('a', 1, 1), ('a', 2, 2)])
        e(V, 'duplicate name', [('b', 1, 1), ('a', 2, 2), ('b', 1, 1)])


def test_order_of_checks():
    ok = ('a', 1, 1)
    err(T, 'nodes: must be an exact list', 'x', 'y')
    err(V, 'nodes: count must be between 1 and 16', [], 'y')
    err(V, 'nodes: count must be between 1 and 16', [None] * 17, 'y')
    err(T, 'nodes: row must be an exact tuple', [None] * 16, 'y')
    err(T, 'containers: must be an exact list', [ok], 'y')
    err(V, 'containers: count must be between 0 and 64', [ok], [None] * 65)
    err(T, 'containers: row must be an exact tuple', [ok], [None] * 64)
    # nodes problems come before containers problems
    err(V, 'nodes: duplicate name', [ok, ok], [None])
    err(T, 'nodes: row must be an exact tuple', [None, ok], 'y')
    # within a row: type, size, name, cpu, mem; rows in order; duplicates last
    err(V, 'nodes: row must have 3 items', [('a', 1), None], 'y')
    err(T, 'nodes: row must be an exact tuple', [None, ('a', 1)], 'y')
    err(V, 'nodes: name must be 1 to 24 lowercase identifier characters', [('A', 'x', 'y')], 'y')
    err(T, 'nodes: name must be an exact string', [(5, 'x', 'y')], 'y')
    err(T, 'nodes: cpu must be a nonbool int', [('a', 'x', 'y')], 'y')
    err(V, 'nodes: cpu must be between 1 and 1000000', [('a', 0, 'y')], 'y')
    err(T, 'nodes: mem must be a nonbool int', [('a', 1, 'y')], 'y')
    err(V, 'nodes: cpu must be between 1 and 1000000', [('a', 0, 'y'), (5, 1, 1)], 'y')
    err(T, 'nodes: name must be an exact string', [(5, 1, 1), ('a', 0, 1)], 'y')
    err(V, 'nodes: duplicate name', [('a', 1, 1), ('a', 1, 1)], [('B', 1, 1)])
    err(V, 'containers: name must be 1 to 24 lowercase identifier characters', [ok], [('a', 1, 1), ('a', 1, 1), ('B', 1, 1)])
    err(V, 'containers: duplicate name', [ok], [('a', 1, 1), ('a', 1, 1)])
