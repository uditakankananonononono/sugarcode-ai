import itertools
import random
import pytest
from sugarcode.extra_doc.root_cause import analyse_causes as ac

T, V = TypeError, ValueError


def oracle(edges, f):
    nodes = sorted({x for e in edges for x in e})
    reach = {(x, y): False for x in nodes for y in nodes}
    for a, b in edges:
        reach[(a, b)] = True
    for k in nodes:
        for i in nodes:
            for j in nodes:
                if reach[(i, k)] and reach[(k, j)]:
                    reach[(i, j)] = True
    anc = [x for x in nodes if reach[(x, f)]]
    roots = [x for x in anc if not any(b == x for _, b in edges)]
    chains = []

    def back(x, tail):
        causes = sorted(a for a, b in edges if b == x)
        if not causes:
            chains.append(tail)
        for c in causes:
            back(c, [c] + tail)
    if anc:
        back(f, [f])
    chains.sort()

    def can(cut):
        keep = [(a, b) for a, b in edges if a not in cut and b not in cut or b == f and a not in cut]
        r2 = {(x, y): False for x in nodes for y in nodes}
        for a, b in keep:
            r2[(a, b)] = True
        for k in nodes:
            for i in nodes:
                for j in nodes:
                    if r2[(i, k)] and r2[(k, j)]:
                        r2[(i, j)] = True
        return any(r2[(r, f)] for r in roots if r not in cut)
    best = []
    for k in range(len(anc) + 1):
        ok = [c for c in itertools.combinations(anc, k) if not can(set(c))]
        if ok:
            best = list(ok[0])
            break
    return {'ancestors': anc, 'roots': roots, 'chains': chains, 'chain_count': len(chains),
            'min_cut': best, 'min_cut_size': len(best)}


def test_hand_case_exact():
    r = ac([('a', 'b'), ('b', 'f'), ('a', 'c'), ('c', 'f'), ('x', 'c')], 'f')
    assert r == {'ancestors': ['a', 'b', 'c', 'x'], 'roots': ['a', 'x'],
                 'chains': [['a', 'b', 'f'], ['a', 'c', 'f'], ['x', 'c', 'f']], 'chain_count': 3,
                 'min_cut': ['a', 'c'], 'min_cut_size': 2}


def test_single_edge_and_effects_after_failure_ignored():
    assert ac([('a', 'f'), ('f', 'z')], 'f') == {'ancestors': ['a'], 'roots': ['a'], 'chains': [['a', 'f']],
                                                  'chain_count': 1, 'min_cut': ['a'], 'min_cut_size': 1}
    r = ac([('z', 'y')], 'z')
    assert r == {'ancestors': [], 'roots': [], 'chains': [], 'chain_count': 0, 'min_cut': [], 'min_cut_size': 0}
    # an unrelated branch does not appear
    assert ac([('a', 'f'), ('q', 'r')], 'f')['ancestors'] == ['a']


def test_chain_of_three_cut_is_alphabetically_first_single_node():
    r = ac([('r', 'm'), ('m', 'n'), ('n', 'f')], 'f')
    assert r['min_cut'] == ['m']
    assert r['roots'] == ['r'] and r['chains'] == [['r', 'm', 'n', 'f']]


def test_bottleneck_cut_smaller_than_roots():
    r = ac([('a', 'm'), ('b', 'm'), ('c', 'm'), ('m', 'f')], 'f')
    assert r['roots'] == ['a', 'b', 'c'] and r['min_cut'] == ['m'] and r['min_cut_size'] == 1
    assert r['chain_count'] == 3


def test_random_dags_vs_oracle():
    rnd = random.Random(463)
    for _ in range(250):
        names = ['n%d' % i for i in range(rnd.randint(2, 8))]
        edges = [(names[i], names[j]) for i in range(len(names)) for j in range(i + 1, len(names)) if rnd.random() < 0.4]
        if not edges:
            continue
        f = rnd.choice(sorted({x for e in edges for x in e}))
        assert ac(edges, f) == oracle(edges, f)
        # shuffled input and a tuple of tuples give the same answer
        sh = edges[:]
        rnd.shuffle(sh)
        assert ac(tuple(tuple(e) for e in sh), f) == ac(edges, f)


def err(f, exc, msg, *a):
    with pytest.raises(exc) as e:
        f(*a)
    assert str(e.value) == msg


OK = [('a', 'f')]
NAME = 'must be 1 to 30 characters from A-Z, a-z, 0-9, _ and -'


def test_pins():
    err(ac, T, 'edges must be a list or tuple', 'ab', 'a')
    err(ac, T, 'edges must be a list or tuple', {('a', 'f')}, 'f')
    err(ac, V, 'edge count must be between 1 and 200', [], 'f')
    err(ac, V, 'edge count must be between 1 and 200', [('a%d' % i, 'f') for i in range(201)], 'f')
    for bad in ('ab', 5, None, ('a',), ('a', 'f', 'g'), {'a': 1, 'b': 2}):
        err(ac, T, 'each edge must be a (cause, effect) pair', [('a', 'f'), bad], 'f')
    err(ac, T, 'cause must be a str', [(1, 'f')], 'f')
    err(ac, T, 'effect must be a str', [('a', 1)], 'f')
    err(ac, T, 'cause must be a str', [(True, 'f')], 'f')
    err(ac, T, 'failure must be a str', OK, 1)
    err(ac, V, 'cause ' + NAME, [('', 'f')], 'f')
    err(ac, V, 'cause ' + NAME, [('a b', 'f')], 'f')
    err(ac, V, 'effect ' + NAME, [('a', 'f.')], 'f')
    err(ac, V, 'cause ' + NAME, [('x' * 31, 'f')], 'f')
    err(ac, V, 'failure ' + NAME, OK, '')
    err(ac, V, 'failure ' + NAME, OK, 'f f')
    err(ac, V, 'an edge cannot join a node to itself', [('a', 'a')], 'a')
    err(ac, V, 'edges must not repeat', [('a', 'f'), ('a', 'f')], 'f')
    err(ac, V, 'failure must appear in an edge', OK, 'zz')
    err(ac, V, 'edges must form an acyclic graph', [('a', 'b'), ('b', 'a'), ('a', 'f')], 'f')
    err(ac, V, 'edges must form an acyclic graph', [('a', 'f'), ('q', 'r'), ('r', 's'), ('s', 'q')], 'f')


def test_boundaries_accepted_and_refused():
    ac([('x' * 30, 'f')], 'f')
    ac([('A-z_9', 'f')], 'f')
    ac([('a%d' % i, 'f') for i in range(12)], 'f')
    err(ac, V, 'at most 12 ancestors are supported', [('a%d' % i, 'f') for i in range(13)], 'f')
    # 200 edges accepted (many unrelated), 201 refused
    ac([('u%d' % i, 'w%d' % i) for i in range(199)] + [('a', 'f')], 'f')
    err(ac, V, 'edge count must be between 1 and 200', [('u%d' % i, 'w%d' % i) for i in range(200)] + [('a', 'f')], 'f')


def test_chain_cap_exact():
    # layers of 2 nodes: 2**k chains through k layers; 2**10 = 1024 > 1000
    def layered(k):
        e = [('r', 'l0a'), ('r', 'l0b')]
        for i in range(k - 1):
            for a in 'ab':
                for b in 'ab':
                    e.append(('l%d%s' % (i, a), 'l%d%s' % (i + 1, b)))
        e += [('l%da' % (k - 1), 'f'), ('l%db' % (k - 1), 'f')]
        return e
    r = ac(layered(4), 'f')
    assert r['chain_count'] == 2 ** 4


def test_chain_cap_boundary_with_ancestor_cap():
    # 5 layers of 2 + root = 11 ancestors, 32 chains: far below the cap, exact count
    e = [('r', 'a0'), ('r', 'b0')]
    for i in range(4):
        for x in 'ab':
            for y in 'ab':
                e.append((x + str(i), y + str(i + 1)))
    e += [('a4', 'f'), ('b4', 'f')]
    assert ac(e, 'f')['chain_count'] == 32
    assert ac(e, 'f')['min_cut'] == ['r']


def test_every_edge_position_validated():
    for pos in range(3):
        e = [('a', 'f'), ('b', 'f'), ('c', 'f')]
        e[pos] = ('x', 7)
        err(ac, T, 'effect must be a str', e, 'f')
        e[pos] = (7, 'f')
        err(ac, T, 'cause must be a str', e, 'f')
        e[pos] = 7
        err(ac, T, 'each edge must be a (cause, effect) pair', e, 'f')


def test_first_problem_reported_in_edge_order():
    err(ac, T, 'cause must be a str', [(1, 'f'), ('a b', 'f')], 'f')
    err(ac, V, 'edges must not repeat', [('a', 'f'), ('a', 'f')], 'f')
    err(ac, T, 'effect must be a str', [('a', 'f'), ('a', 3)], 'f')
    # failure type is checked after the edges, before presence
    err(ac, T, 'failure must be a str', OK, None)


EDGES_1000 = [('n00', 'n02'), ('n00', 'n04'), ('n00', 'n05'), ('n00', 'n06'), ('n00', 'n08'), ('n00', 'n09'), ('n00', 'n10'), ('n00', 'n11'), ('n01', 'n03'), ('n01', 'n04'), ('n01', 'n05'), ('n01', 'n06'), ('n01', 'n07'), ('n01', 'n08'), ('n01', 'n09'), ('n01', 'n10'), ('n02', 'n03'), ('n02', 'n04'), ('n02', 'n05'), ('n02', 'n06'), ('n02', 'n07'), ('n02', 'n08'), ('n02', 'n09'), ('n02', 'n10'), ('n02', 'n11'), ('n03', 'n04'), ('n03', 'n05'), ('n03', 'n06'), ('n03', 'n07'), ('n03', 'n08'), ('n03', 'n09'), ('n03', 'n10'), ('n03', 'n11'), ('n04', 'n05'), ('n04', 'n06'), ('n04', 'n07'), ('n04', 'n08'), ('n04', 'n09'), ('n04', 'n10'), ('n04', 'n11'), ('n05', 'n06'), ('n05', 'n07'), ('n05', 'n08'), ('n05', 'n09'), ('n05', 'n11'), ('n06', 'n07'), ('n06', 'n08'), ('n06', 'n09'), ('n06', 'n10'), ('n06', 'n11'), ('n07', 'n08'), ('n07', 'n09'), ('n07', 'n11'), ('n08', 'n09'), ('n08', 'n11'), ('n09', 'n10'), ('n09', 'n11'), ('n10', 'n11'), ('n01', 'f'), ('n03', 'f'), ('n05', 'f'), ('n06', 'f'), ('n07', 'f'), ('n08', 'f'), ('n09', 'f'), ('n10', 'f'), ('n11', 'f')]
EDGES_1001 = [('n00', 'n01'), ('n00', 'n02'), ('n00', 'n03'), ('n00', 'n04'), ('n00', 'n05'), ('n00', 'n06'), ('n00', 'n07'), ('n00', 'n08'), ('n00', 'n09'), ('n00', 'n10'), ('n00', 'n11'), ('n01', 'n02'), ('n01', 'n03'), ('n01', 'n04'), ('n01', 'n05'), ('n01', 'n06'), ('n01', 'n07'), ('n01', 'n08'), ('n01', 'n09'), ('n01', 'n10'), ('n01', 'n11'), ('n02', 'n03'), ('n02', 'n04'), ('n02', 'n07'), ('n02', 'n08'), ('n02', 'n09'), ('n02', 'n10'), ('n03', 'n05'), ('n03', 'n06'), ('n03', 'n07'), ('n03', 'n08'), ('n03', 'n09'), ('n03', 'n10'), ('n03', 'n11'), ('n04', 'n05'), ('n04', 'n06'), ('n04', 'n07'), ('n04', 'n08'), ('n04', 'n09'), ('n04', 'n11'), ('n05', 'n06'), ('n05', 'n08'), ('n05', 'n09'), ('n05', 'n10'), ('n05', 'n11'), ('n06', 'n07'), ('n06', 'n08'), ('n06', 'n09'), ('n06', 'n10'), ('n06', 'n11'), ('n07', 'n08'), ('n07', 'n09'), ('n07', 'n10'), ('n07', 'n11'), ('n08', 'n09'), ('n08', 'n11'), ('n09', 'n10'), ('n09', 'n11'), ('n10', 'n11'), ('n00', 'f'), ('n02', 'f'), ('n03', 'f'), ('n05', 'f'), ('n07', 'f'), ('n08', 'f'), ('n09', 'f'), ('n10', 'f'), ('n11', 'f')]


def test_chain_cap_exactly_1000_accepted_1001_refused():
    r = ac(EDGES_1000, 'f')
    assert r['chain_count'] == 1000 and len(r['chains']) == 1000
    assert r['chain_count'] == oracle(EDGES_1000, 'f')['chain_count']
    err(ac, V, 'too many causal chains', EDGES_1001, 'f')
    assert len(oracle(EDGES_1001, 'f')['chains']) == 1001


def test_dead_branches_do_not_blow_up():
    # 40 diamond layers behind the failure: r reaches f directly; a/b nodes cannot reach f at all.
    # A traversal that explores dead branches takes 2**40 steps; this must return quickly.
    e = [('r', 'f'), ('r', 'a00'), ('r', 'b00')]
    for i in range(1, 40):
        for x in ('a%02d' % (i - 1), 'b%02d' % (i - 1)):
            e.append((x, 'a%02d' % i))
            e.append((x, 'b%02d' % i))
    assert len(e) == 159
    r = ac(e, 'f')
    assert r == {'ancestors': ['r'], 'roots': ['r'], 'chains': [['r', 'f']], 'chain_count': 1,
                 'min_cut': ['r'], 'min_cut_size': 1}


def test_cut_may_use_a_middle_node_beside_a_root_only_path():
    # z -> m -> f is blocked by m (sorts before z); y -> f is a separate direct path and needs y itself
    r = ac([('z', 'm'), ('m', 'f'), ('y', 'f')], 'f')
    assert r['roots'] == ['y', 'z'] and r['min_cut'] == ['m', 'y'] and r['min_cut_size'] == 2
    assert r == oracle([('z', 'm'), ('m', 'f'), ('y', 'f')], 'f')
    # the cut node must really block: with m removed, z cannot reach f through another way
    r = ac([('z', 'm'), ('m', 'n'), ('n', 'f'), ('y', 'f')], 'f')
    assert r['min_cut'] == ['m', 'y']


def test_ancestor_search_visits_each_node_once_on_deep_diamonds():
    import time
    e = []
    for i in range(1, 48):
        for x in 'ab':
            for y in 'ab':
                e.append(('l%02d%s' % (i - 1, x), 'l%02d%s' % (i, y)))
    e += [('l47a', 'f'), ('l47b', 'f')]
    t0 = time.time()
    err(ac, V, 'at most 12 ancestors are supported', e, 'f')
    assert time.time() - t0 < 3


@pytest.mark.parametrize('fail', ['A', 'f', 'zz'])
def test_cut_search_visits_each_node_once_behind_dead_diamonds(fail):
    import time
    e = [('r', fail), ('r', 'a00'), ('r', 'b00')]
    for i in range(1, 30):
        for x in 'ab':
            for y in 'ab':
                e.append(('%s%02d' % (x, i - 1), '%s%02d' % (y, i)))
    import signal

    def boom(*_):
        raise AssertionError('cut search took more than 5 seconds')
    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(5)
    try:
        t0 = time.time()
        r = ac(e, fail)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)
    assert time.time() - t0 < 3
    assert r == {'ancestors': ['r'], 'roots': ['r'], 'chains': [['r', fail]], 'chain_count': 1,
                 'min_cut': ['r'], 'min_cut_size': 1}
