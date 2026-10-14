import itertools
import random
import pytest
from sugarcode.extra_doc.domain_driven_design import check_layers as cl

T, V = TypeError, ValueError
LAYERS = ['domain', 'application', 'infrastructure', 'interface']


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


def oracle(modules, deps):
    layer = dict(modules)
    names = sorted(layer)
    # the allowed table written out as a matrix of yes/no, row = user layer, column = used layer
    ok = {('domain', 'domain'): 1, ('application', 'application'): 1, ('application', 'domain'): 1,
          ('infrastructure', 'infrastructure'): 1, ('infrastructure', 'application'): 1, ('infrastructure', 'domain'): 1,
          ('interface', 'interface'): 1, ('interface', 'application'): 1, ('interface', 'domain'): 1}
    viol = sorted((u, v, layer[u] + '_uses_' + layer[v]) for u, v in deps if not ok.get((layer[u], layer[v])))
    reach = {(a, b): (a, b) in set(deps) for a in names for b in names}       # transitive closure, Warshall
    for k in names:
        for a in names:
            for b in names:
                if reach[(a, k)] and reach[(k, b)]:
                    reach[(a, b)] = True
    return {'violations': viol, 'cycles': [n for n in names if reach[(n, n)]],
            'by_layer': {l: sorted(n for n in names if layer[n] == l) for l in LAYERS}}


def test_hand_cases():
    mods = [('order', 'domain'), ('billing', 'application'), ('db', 'infrastructure'), ('web', 'interface')]
    deps = [('web', 'billing'), ('billing', 'order'), ('db', 'order'), ('db', 'billing')]
    assert cl(mods, deps) == {'violations': [], 'cycles': [],
                              'by_layer': {'domain': ['order'], 'application': ['billing'], 'infrastructure': ['db'],
                                           'interface': ['web']}}
    r = cl(mods, [('order', 'db'), ('billing', 'web'), ('web', 'db'), ('db', 'web'), ('order', 'billing')])
    assert r['violations'] == [('billing', 'web', 'application_uses_interface'), ('db', 'web', 'infrastructure_uses_interface'),
                               ('order', 'billing', 'domain_uses_application'), ('order', 'db', 'domain_uses_infrastructure'),
                               ('web', 'db', 'interface_uses_infrastructure')]
    assert r['cycles'] == ['db', 'web']
    r = cl([('a', 'domain')], [('a', 'a')])
    assert r['cycles'] == ['a'] and r['violations'] == []
    r = cl([('a', 'domain'), ('b', 'domain'), ('c', 'domain')], [('a', 'b'), ('b', 'c'), ('c', 'a')])
    assert r['cycles'] == ['a', 'b', 'c']
    r = cl([('a', 'domain'), ('b', 'domain'), ('c', 'domain')], [('a', 'b'), ('b', 'c'), ('a', 'c')])
    assert r['cycles'] == []
    r = cl([('a', 'domain'), ('b', 'domain'), ('c', 'domain'), ('d', 'domain')], [('a', 'b'), ('b', 'a'), ('c', 'a')])
    assert r['cycles'] == ['a', 'b']                       # c reaches a cycle but is not on it
    assert cl([('a', 'domain')], [])['by_layer'] == {'domain': ['a'], 'application': [], 'infrastructure': [], 'interface': []}
    # every pair of layers
    allowed = {('domain', 'domain'), ('application', 'application'), ('application', 'domain'), ('infrastructure', 'infrastructure'),
               ('infrastructure', 'application'), ('infrastructure', 'domain'), ('interface', 'interface'),
               ('interface', 'application'), ('interface', 'domain')}
    for l1, l2 in itertools.product(LAYERS, repeat=2):
        r = cl([('x', l1), ('y', l2)], [('x', 'y')])
        assert (r['violations'] == []) == ((l1, l2) in allowed)
        if (l1, l2) not in allowed:
            assert r['violations'] == [('x', 'y', l1 + '_uses_' + l2)]


def test_random_vs_warshall_oracle():
    rnd = random.Random(671)
    cyc = viol = 0
    for _ in range(500):
        n = rnd.randint(1, 7)
        names = ['m%d' % i for i in range(n)]
        mods = [(x, rnd.choice(LAYERS)) for x in names]
        pairs = [(a, b) for a in names for b in names]
        deps = rnd.sample(pairs, rnd.randint(0, min(len(pairs), 10)))
        rnd.shuffle(mods)
        r = cl(mods, deps)
        assert r == oracle(mods, deps)
        cyc += bool(r['cycles'])
        viol += bool(r['violations'])
    assert cyc > 100 and viol > 100


def test_limits_accepted():
    names = ['m%02d' % i for i in range(32)]
    mods = [(n, 'domain') for n in names]
    deps = [(a, b) for a in names[:10] for b in names[:10]][:96]
    r = cl(mods, deps)
    assert len(deps) == 96 and r['cycles'] == sorted(names[:10])
    cl([('a' * 24, 'domain')], [])


def err(exc, msg, mods, deps):
    with pytest.raises(exc) as e:
        cl(mods, deps)
    assert str(e.value) == msg


OKM = [('a', 'domain'), ('b', 'application')]
LMSG = "layer must be 'domain', 'application', 'infrastructure' or 'interface'"


def test_pins():
    for bad in (None, (), 'ab', ListSub(OKM), {}):
        err(T, 'modules must be an exact list', bad, [])
    err(V, 'module count must be between 1 and 32', [], [])
    err(V, 'module count must be between 1 and 32', [('m%02d' % i, 'domain') for i in range(33)], [])
    for bad in (None, ['a', 'domain'], 'ab', TupleSub(('a', 'domain')), 5):
        err(T, 'each module must be an exact tuple', [bad], [])
    for bad in ((), ('a',), ('a', 'domain', 1)):
        err(V, 'each module must have 2 items', [bad], [])
    for bad in (None, 5, b'a', StrSub('a')):
        err(T, 'name must be an exact string', [(bad, 'domain')], [])
        err(T, 'name must be an exact string', OKM, [(bad, 'a')])
        err(T, 'name must be an exact string', OKM, [('a', bad)])
    for bad in ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a'):
        err(V, 'name must be 1 to 24 lowercase identifier characters', [(bad, 'domain')], [])
        err(V, 'name must be 1 to 24 lowercase identifier characters', OKM, [(bad, 'a')])
        err(V, 'name must be 1 to 24 lowercase identifier characters', OKM, [('a', bad)])
    for bad in (None, 5, b'domain', StrSub('domain')):
        err(T, 'layer must be an exact string', [('a', bad)], [])
    for bad in ('', 'Domain', 'domain ', 'ui', 'core', 'infra'):
        err(V, LMSG, [('a', bad)], [])
    err(V, 'duplicate module name', [('a', 'domain'), ('a', 'application')], [])
    for bad in (None, (), 'ab', ListSub([('a', 'b')]), {}):
        err(T, 'dependencies must be an exact list', OKM, bad)
    err(V, 'dependency count must be at most 96', OKM, [('a', 'b')] * 97)
    for bad in (None, ['a', 'b'], 'ab', TupleSub(('a', 'b')), 5):
        err(T, 'each dependency must be an exact tuple', OKM, [bad])
    for bad in ((), ('a',), ('a', 'b', 'a')):
        err(V, 'each dependency must have 2 items', OKM, [bad])
    err(V, 'duplicate dependency', OKM, [('a', 'b'), ('b', 'a'), ('a', 'b')])
    err(V, 'unknown module: z', OKM, [('z', 'a')])
    err(V, 'unknown module: z', OKM, [('a', 'z')])
    err(V, 'unknown module: y', OKM, [('y', 'z')])
    err(V, 'unknown module: q', OKM, [('a', 'q'), ('y', 'a')])


def test_order_of_checks():
    err(T, 'modules must be an exact list', 'x', 'y')
    err(V, 'module count must be between 1 and 32', [], 'y')
    err(V, 'module count must be between 1 and 32', [None] * 33, 'y')
    err(T, 'each module must be an exact tuple', [None, ('a',)], 'y')
    err(V, 'each module must have 2 items', [('a',), None], 'y')
    err(V, 'name must be 1 to 24 lowercase identifier characters', [('A', 5)], 'y')
    err(T, 'name must be an exact string', [(5, 'zz')], 'y')
    err(T, 'layer must be an exact string', [('a', 5)], 'y')
    err(V, LMSG, [('a', 'zz'), (5, 'x')], 'y')
    err(T, 'name must be an exact string', [(5, 'x'), ('a', 'zz')], 'y')
    err(V, 'duplicate module name', [('a', 'domain'), ('a', 'domain')], 'y')
    err(T, 'dependencies must be an exact list', OKM, 'y')
    err(V, 'dependency count must be at most 96', OKM, [None] * 97)
    err(T, 'each dependency must be an exact tuple', OKM, [None, ('a',)])
    err(V, 'each dependency must have 2 items', OKM, [('a',), None])
    err(V, 'name must be 1 to 24 lowercase identifier characters', OKM, [('A', 5)])
    err(T, 'name must be an exact string', OKM, [(5, 'A')])
    err(T, 'name must be an exact string', OKM, [('a', 5)])
    err(V, 'name must be 1 to 24 lowercase identifier characters', OKM, [('a', 'A')])
    err(V, 'duplicate dependency', OKM, [('z', 'z'), ('z', 'z')])                  # before unknown names
    err(V, 'unknown module: q', OKM, [('q', 'z'), ('a', 'z')])
