import random
import pytest
from sugarcode.extra_doc.functional_core_imperative_shell import check_purity as cp

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


def oracle(funcs, calls, effects):
    zone = dict(funcs)
    reach = {n: {n} for n in zone}                      # fixpoint, not a graph walk
    changed = True
    while changed:
        changed = False
        for a, b in calls:
            if not reach[b] <= reach[a]:
                reach[a] |= reach[b]
                changed = True
    return {'core_calls_shell': sorted((a, b) for a, b in calls if zone[a] == 'core' and zone[b] == 'shell'),
            'core_effects': sorted(e for e in effects if zone[e] == 'core'),
            'tainted': sorted(n for n in zone if zone[n] == 'core' and any(e in reach[n] for e in effects))}


def test_hand_cases():
    f = [('calc', 'core'), ('fmt', 'core'), ('main', 'shell'), ('save', 'shell')]
    assert cp(f, [('main', 'calc'), ('main', 'save'), ('calc', 'fmt')], ['save']) == {
        'core_calls_shell': [], 'core_effects': [], 'tainted': []}
    r = cp(f, [('calc', 'fmt'), ('fmt', 'save'), ('calc', 'main')], ['save'])
    assert r == {'core_calls_shell': [('calc', 'main'), ('fmt', 'save')], 'core_effects': [], 'tainted': ['calc', 'fmt']}
    r = cp(f, [], ['fmt', 'save'])
    assert r['core_effects'] == ['fmt'] and r['tainted'] == ['fmt']
    r = cp([('a', 'core'), ('b', 'core'), ('c', 'core')], [('a', 'b'), ('b', 'c'), ('c', 'a')], ['c'])
    assert r['tainted'] == ['a', 'b', 'c']                           # a cycle does not hang and reaches the effect
    r = cp([('a', 'core'), ('b', 'core')], [('a', 'a'), ('b', 'a')], [])
    assert r['tainted'] == []
    r = cp([('a', 'shell'), ('b', 'core')], [('a', 'b')], ['a'])
    assert r['tainted'] == []                                         # a shell caller is not a tainted callee
    assert cp([('a', 'core')], [], []) == {'core_calls_shell': [], 'core_effects': [], 'tainted': []}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(6830 + part)
    c1 = c2 = c3 = 0
    for _ in range(60):
        n = rnd.randint(1, 7)
        names = ['f%d' % i for i in range(n)]
        funcs = [(x, rnd.choice(['core', 'core', 'shell'])) for x in names]
        pairs = [(a, b) for a in names for b in names]
        calls = rnd.sample(pairs, rnd.randint(0, min(9, len(pairs))))
        effects = rnd.sample(names, rnd.randint(0, min(2, n)))
        r = cp(funcs, calls, effects)
        assert r == oracle(funcs, calls, effects)
        c1 += bool(r['core_calls_shell'])
        c2 += bool(r['core_effects'])
        c3 += bool(r['tainted'])
    assert c1 > 5 and c2 > 5 and c3 > 5


def test_limits_accepted():
    names = ['f%02d' % i for i in range(32)]
    funcs = [(n, 'core') for n in names]
    calls = [(x, y) for x in names[:10] for y in names[:10]][:96]
    assert len(calls) == 96
    r = cp(funcs, calls, names)
    assert r['tainted'] == names and r['core_effects'] == names and r['core_calls_shell'] == []
    cp([('a' * 24, 'core')], [], ['a' * 24])


def err(exc, msg, f, c, e):
    with pytest.raises(exc) as x:
        cp(f, c, e)
    assert str(x.value) == msg


F = [('a', 'core'), ('b', 'shell')]
NM = 'name must be 1 to 24 lowercase identifier characters'
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')
NS = (None, 5, b'a', StrSub('a'))


def _pins(err):
    for bad in (None, (), 'ab', ListSub(F), {}):
        err(T, 'functions must be an exact list', bad, [], [])
    err(V, 'function count must be between 1 and 32', [], [], [])
    err(V, 'function count must be between 1 and 32', [('f%02d' % i, 'core') for i in range(33)], [], [])
    for bad in (None, ['a', 'core'], 'ab', TupleSub(('a', 'core')), 5):
        err(T, 'each function must be an exact tuple', [bad], [], [])
    for bad in ((), ('a',), ('a', 'core', 1)):
        err(V, 'each function must have 2 items', [bad], [], [])
    for bad in NS:
        err(T, 'name must be an exact string', [(bad, 'core')], [], [])
        err(T, 'name must be an exact string', F, [(bad, 'a')], [])
        err(T, 'name must be an exact string', F, [('a', bad)], [])
        err(T, 'name must be an exact string', F, [], [bad])
    for bad in BAD:
        err(V, NM, [(bad, 'core')], [], [])
        err(V, NM, F, [(bad, 'a')], [])
        err(V, NM, F, [('a', bad)], [])
        err(V, NM, F, [], [bad])
    for bad in (None, 5, b'core', StrSub('core')):
        err(T, 'zone must be an exact string', [('a', bad)], [], [])
    for bad in ('', 'Core', 'core ', 'pure', 'edge'):
        err(V, "zone must be 'core' or 'shell'", [('a', bad)], [], [])
    err(V, 'duplicate function name', [('a', 'core'), ('a', 'shell')], [], [])
    for bad in (None, (), 'ab', ListSub([('a', 'b')]), {}):
        err(T, 'calls must be an exact list', F, bad, [])
    err(V, 'call count must be at most 96', F, [('a', 'b')] * 97, [])
    for bad in (None, ['a', 'b'], 'ab', TupleSub(('a', 'b')), 5):
        err(T, 'each call must be an exact tuple', F, [bad], [])
    for bad in ((), ('a',), ('a', 'b', 'a')):
        err(V, 'each call must have 2 items', F, [bad], [])
    err(V, 'duplicate call', F, [('a', 'b'), ('b', 'a'), ('a', 'b')], [])
    err(V, 'unknown function: z', F, [('z', 'a')], [])
    err(V, 'unknown function: z', F, [('a', 'z')], [])
    err(V, 'unknown function: y', F, [('y', 'z')], [])
    for bad in (None, (), 'ab', ListSub(['a']), {}):
        err(T, 'effects must be an exact list', F, [], bad)
    err(V, 'effect count must be at most 32', F, [], ['f%02d' % i for i in range(33)])
    err(V, 'repeated effect', F, [], ['a', 'b', 'a'])
    err(V, 'unknown function: z', F, [], ['z'])


def _order(err):
    err(T, 'functions must be an exact list', 'x', 'y', 'z')
    err(V, 'function count must be between 1 and 32', [], 'y', 'z')
    err(V, 'function count must be between 1 and 32', [None] * 33, 'y', 'z')
    err(T, 'each function must be an exact tuple', [None, ('a',)], 'y', 'z')
    err(V, 'each function must have 2 items', [('a',), None], 'y', 'z')
    err(V, NM, [('A', 5)], 'y', 'z')
    err(T, 'name must be an exact string', [(5, 'zz')], 'y', 'z')
    err(T, 'zone must be an exact string', [('a', 5)], 'y', 'z')
    err(V, "zone must be 'core' or 'shell'", [('a', 'zz'), (5, 'x')], 'y', 'z')
    err(T, 'name must be an exact string', [(5, 'x'), ('a', 'zz')], 'y', 'z')
    err(V, 'duplicate function name', [('a', 'core'), ('a', 'core')], 'y', 'z')
    err(T, 'calls must be an exact list', F, 'y', 'z')
    err(V, 'call count must be at most 96', F, [None] * 97, 'z')
    err(T, 'each call must be an exact tuple', F, [None, ('a',)], 'z')
    err(V, 'each call must have 2 items', F, [('a',), None], 'z')
    err(V, NM, F, [('A', 5)], 'z')
    err(T, 'name must be an exact string', F, [(5, 'A')], 'z')
    err(T, 'name must be an exact string', F, [('a', 5)], 'z')
    err(V, NM, F, [('a', 'A')], 'z')
    err(V, 'duplicate call', F, [('q', 'q'), ('q', 'q')], 'z')
    err(V, 'unknown function: q', F, [('q', 'z'), ('a', 'z')], 'z')
    err(T, 'effects must be an exact list', F, [], 'z')
    err(V, 'effect count must be at most 32', F, [], [None] * 33)
    err(T, 'name must be an exact string', F, [], [5, 'A'])
    err(V, NM, F, [], ['A', 5])
    err(V, 'repeated effect', F, [], ['q', 'q'])
    err(V, 'unknown function: q', F, [], ['q', 'z'])


def _collect(fn):
    out = []

    def rec(exc, msg, *a):
        out.append((exc, msg) + a)
    fn(rec)
    return out


@pytest.mark.parametrize('exc,msg,f,c,e', _collect(_pins))
def test_pin(exc, msg, f, c, e):
    err(exc, msg, f, c, e)


@pytest.mark.parametrize('exc,msg,f,c,e', _collect(_order))
def test_order(exc, msg, f, c, e):
    err(exc, msg, f, c, e)


def test_tainted_is_sorted_not_walk_order():
    r = cp([('b', 'core'), ('a', 'core')], [('b', 'a')], ['a'])
    assert r == {'core_calls_shell': [], 'core_effects': ['a'], 'tainted': ['a', 'b']}
