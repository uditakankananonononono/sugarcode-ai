import itertools
import random
import pytest
from sugarcode.extra_doc.iac_plan import plan_changes as plan

T, V = TypeError, ValueError


class StrSub(str):
    pass


class IntSub(int):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


def smallest_order(rows):
    # brute force over every permutation: the smallest list in which each resource follows all it depends on
    names = sorted(n for n, _, _ in rows)
    deps = {n: set(d) for n, _, d in rows}
    for perm in itertools.permutations(names):             # permutations come out in lexicographic order
        pos = {n: i for i, n in enumerate(perm)}
        if all(pos[d] < pos[n] for n in perm for d in deps[n]):
            return list(perm)
    return None


def oracle(cur, des):
    c = {n: (s, set(d)) for n, s, d in cur}
    d = {n: (s, set(x)) for n, s, x in des}
    order = smallest_order(des)
    corder = smallest_order(cur)
    gone = sorted(set(c) - set(d))
    return {'create': [n for n in order if n not in c],
            'update': [n for n in order if n in c and c[n] != d[n]],
            'unchanged': sorted(n for n in d if n in c and c[n] == d[n]),
            'delete': gone, 'order': order,
            'delete_order': [n for n in reversed(corder) if n in gone]}


def test_hand_cases():
    cur = [('db', 1, ()), ('app', 1, ('db',)), ('old', 5, ())]
    des = [('app', 2, ('db', 'cache')), ('cache', 1, ()), ('db', 1, ())]
    assert plan(cur, des) == {'create': ['cache'], 'update': ['app'], 'unchanged': ['db'], 'delete': ['old'],
                              'order': ['cache', 'db', 'app'], 'delete_order': ['old']}
    assert plan([], []) == {'create': [], 'update': [], 'unchanged': [], 'delete': [], 'order': [], 'delete_order': []}
    assert plan([], [('a', 1, ())])['create'] == ['a']
    r = plan([('a', 1, ()), ('b', 1, ('a',)), ('c', 1, ('b',))], [])
    assert r['delete'] == ['a', 'b', 'c'] and r['delete_order'] == ['c', 'b', 'a']
    # a dependency change alone is an update, and the dependency order does not matter
    assert plan([('a', 1, ()), ('b', 1, ())], [('a', 1, ()), ('b', 1, ('a',))])['update'] == ['b']
    assert plan([('a', 1, ()), ('b', 1, ('a',)), ('c', 1, ())], [('a', 1, ()), ('b', 1, ('a',)), ('c', 1, ())])['unchanged'] == ['a', 'b', 'c']
    r = plan([('a', 1, ()), ('b', 1, ()), ('c', 1, ('a', 'b'))], [('a', 1, ()), ('b', 1, ()), ('c', 1, ('b', 'a'))])
    assert r['update'] == [] and r['unchanged'] == ['a', 'b', 'c']
    # smallest order: 'a' waits for 'z'; every other free name goes first when it sorts earlier
    assert plan([], [('a', 1, ('z',)), ('m', 1, ()), ('z', 1, ())])['order'] == ['m', 'z', 'a']
    assert plan([], [('b', 1, ()), ('a', 1, ('b',)), ('c', 1, ())])['order'] == ['b', 'a', 'c']


def rand_graph(rnd, names, p):
    rows = []
    for i, n in enumerate(names):
        deps = tuple(sorted(d for d in names[:i] if rnd.random() < p))      # only earlier names: acyclic
        rows.append([n, rnd.randint(0, 2), deps])
    perm = names[:]
    rnd.shuffle(perm)                                                       # rows are then shuffled
    out = [tuple(r) for r in rows]
    rnd.shuffle(out)
    return out


def test_random_vs_brute_force_oracle():
    rnd = random.Random(612)
    for _ in range(300):
        pool = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        cur_names = rnd.sample(pool, rnd.randint(0, 6))
        des_names = rnd.sample(pool, rnd.randint(0, 6))
        # a random topological labelling per list, with shuffled names
        cur = rand_graph(rnd, cur_names, 0.4)
        des = rand_graph(rnd, des_names, 0.4)
        got = plan(cur, des)
        assert got == oracle(cur, des)
        assert sorted(got['create'] + got['update'] + got['unchanged']) == sorted(n for n, _, _ in des)
        assert sorted(got['unchanged'] + got['update'] + got['delete']) == sorted({n for n, _, _ in cur})
    cur, des = [('a', 1, ())], [('a', 1, ())]
    plan(cur, des)
    assert cur == [('a', 1, ())] and des == [('a', 1, ())]


def test_caps_and_edges():
    names = ['r%02d' % i for i in range(32)]
    chain = [(names[i], 0, (names[i - 1],) if i else ()) for i in range(32)]
    r = plan(chain, chain)
    assert r['order'] == names and r['unchanged'] == names
    assert plan(chain[::-1], [])['delete_order'] == names[::-1]
    with pytest.raises(V, match='^current: at most 32 resources$'):
        plan([('a', 0, ())] * 33, [])
    with pytest.raises(V, match='^desired: at most 32 resources$'):
        plan([], [('a', 0, ())] * 33)
    plan([('a', 0, ())], [('a', 1000000, ())])
    plan([('a', -1000000, ())], [])
    deps8 = tuple('d%d' % i for i in range(8))
    rows = [('d%d' % i, 0, ()) for i in range(8)] + [('top', 0, deps8)]
    assert plan([], rows)['order'][-1] == 'top'
    plan([('a', 0, ()), ('b', 0, ('a',))], [])
    plan([('a' * 24, 0, ())], [('a' * 24, 1, ())])


def err(exc, msg, cur, des):
    with pytest.raises(exc) as e:
        plan(cur, des)
    assert str(e.value) == msg


def test_pins_every_slot_for_both_lists():
    ok = ('a', 1, ())
    for which in ('current', 'desired'):
        def e(exc, msg, rows, which=which):
            err(exc, which + ': ' + msg, *((rows, []) if which == 'current' else ([], rows)))
        for bad in (None, (), 'x', {1}):
            e(T, 'must be an exact list', bad)
        e(T, 'must be an exact list', ListSub([ok]))
        for bad in (None, [], 'abc', TupleSub(ok), 5):
            e(T, 'resource must be an exact tuple', [bad])
        for bad_row in ((), ('a',), ('a', 1), ('a', 1, (), 0)):
            e(V, 'resource must have 3 items', [bad_row])
        for bad in (None, 5, b'a', StrSub('a'), ['a']):
            e(T, 'name must be an exact string', [(bad, 1, ())])
        for bad in ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a'):
            e(V, 'name must be 1 to 24 lowercase identifier characters', [(bad, 1, ())])
        for bad in (True, 1.0, '1', None, IntSub(1), [1]):
            e(T, 'spec must be a nonbool int', [('a', bad, ())])
        for bad in (1000001, -1000001):
            e(V, 'spec must be between -1000000 and 1000000', [('a', bad, ())])
        for bad in (None, [], 'a', TupleSub(), {'a'}, ListSub()):
            e(T, 'deps must be an exact tuple', [('a', 1, bad)])
        e(V, 'at most 8 deps', [('a', 1, tuple('d%d' % i for i in range(9)))])
        for bad in (None, 5, StrSub('b'), b'b'):
            e(T, 'name must be an exact string', [('a', 1, (bad,))])
        e(V, 'name must be 1 to 24 lowercase identifier characters', [('a', 1, ('B',))])
        e(V, 'duplicate name', [('a', 1, ()), ('a', 2, ())])
        e(V, 'duplicate dependency', [('a', 1, ()), ('b', 1, ('a', 'a'))])
        e(V, 'unknown dependency', [('a', 1, ('x',))])
        e(V, 'resource depends on itself', [('a', 1, ('a',))])
        e(V, 'dependency cycle', [('a', 1, ('b',)), ('b', 1, ('a',))])
        e(V, 'dependency cycle', [('a', 1, ('c',)), ('b', 1, ('a',)), ('c', 1, ('b',)), ('z', 0, ())])


def test_order_of_checks():
    # lists are looked at in order: current's problems come before desired's
    err(V, 'current: duplicate name', [('a', 1, ()), ('a', 1, ())], [('a', 1, ('x',))])
    err(T, 'current: must be an exact list', 'x', 'y')
    err(T, 'desired: must be an exact list', [], 'y')
    err(V, 'current: at most 32 resources', [None] * 33, 'y')
    err(T, 'current: resource must be an exact tuple', [None] * 32, 'y')
    # inside one list: size, then each row (type, size, name, spec, deps type, count, dep names), then duplicates...
    row = ('a', 1, ())
    err(T, 'desired: resource must be an exact tuple', [], [None] * 5 + [row] * 3)
    err(V, 'desired: resource must have 3 items', [], [('a', 1), None])
    err(T, 'desired: resource must be an exact tuple', [], [None, ('a', 1)])
    err(V, 'desired: name must be 1 to 24 lowercase identifier characters', [], [('A', 'x', 'y')])
    err(T, 'desired: name must be an exact string', [], [(5, 'x', 'y')])
    err(T, 'desired: spec must be a nonbool int', [], [('a', 'x', 'y')])
    err(V, 'desired: spec must be between -1000000 and 1000000', [], [('a', 10 ** 9, 'y')])
    err(T, 'desired: deps must be an exact tuple', [], [('a', 1, 'y')])
    err(V, 'desired: at most 8 deps', [], [('a', 1, ('B',) * 9)])
    err(V, 'desired: name must be 1 to 24 lowercase identifier characters', [], [('a', 1, ('B', 5))])
    err(T, 'desired: name must be an exact string', [], [('a', 1, (5, 'B'))])
    err(V, 'desired: spec must be between -1000000 and 1000000', [], [('a', 10 ** 9, ()), (5, 1, ())])
    err(T, 'desired: name must be an exact string', [], [(5, 1, ()), ('a', 10 ** 9, ())])
    # then duplicates, duplicated dependencies, unknown, self, cycle
    err(V, 'desired: duplicate name', [], [('a', 1, ('a', 'a')), ('a', 1, ())])
    err(V, 'desired: duplicate dependency', [], [('b', 1, ('a', 'a')), ('a', 1, ('zz',))])
    err(V, 'desired: duplicate dependency', [], [('a', 1, ('a', 'a'))])
    err(V, 'desired: unknown dependency', [], [('a', 1, ('a', 'x'))])
    err(V, 'desired: unknown dependency', [], [('a', 1, ('b',)), ('b', 1, ('b', 'q'))])
    err(V, 'desired: resource depends on itself', [], [('a', 1, ('b',)), ('b', 1, ('b',))])
    err(V, 'desired: dependency cycle', [], [('a', 1, ('b',)), ('b', 1, ('a',))])
