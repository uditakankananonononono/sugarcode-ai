import random
import pytest
from sugarcode.extra_doc.ontology_check import check_ontology as oc

T, V = TypeError, ValueError


def oracle(subs, dis, inst):
    names = sorted({x for p in subs for x in p} | {x for p in dis for x in p} | {c for _, c in inst})
    up = {(a, b): False for a in names for b in names}
    for c, p in subs:
        up[(c, p)] = True
    for k in names:
        for i in names:
            for j in names:
                if up[(i, k)] and up[(k, j)]:
                    up[(i, j)] = True
    if any(up[(c, c)] for c in names):
        return None
    below = {c: sorted(p for p in names if up[(c, p)]) for c in names}
    sat = lambda c, a: a == c or up[(c, a)]
    unsat = [c for c in names if any(sat(c, a) and sat(c, b) for a, b in dis)]
    inds = sorted({i for i, _ in inst})
    ty = {i: sorted({a for ii, c in inst if ii == i for a in names if sat(c, a)}) for i in inds}
    viol = []
    for i in inds:
        for a, b in dis:
            if a in ty[i] and b in ty[i]:
                viol.append([i] + sorted([a, b]))
    viol.sort()
    return {'classes': names, 'ancestors': below, 'unsatisfiable': unsat, 'instance_types': ty,
            'violations': viol, 'consistent': not viol}


def test_hand_case_exact():
    r = oc([('dog', 'mammal'), ('mammal', 'animal'), ('cat', 'mammal'), ('plant', 'life'), ('animal', 'life')],
           [('animal', 'plant'), ('dog', 'cat')], [('rex', 'dog'), ('x', 'plant'), ('y', 'cat'), ('y', 'dog')])
    assert r['classes'] == ['animal', 'cat', 'dog', 'life', 'mammal', 'plant']
    assert r['ancestors'] == {'animal': ['life'], 'cat': ['animal', 'life', 'mammal'], 'dog': ['animal', 'life', 'mammal'],
                              'life': [], 'mammal': ['animal', 'life'], 'plant': ['life']}
    assert r['unsatisfiable'] == []
    assert r['instance_types'] == {'rex': ['animal', 'dog', 'life', 'mammal'], 'x': ['life', 'plant'],
                                   'y': ['animal', 'cat', 'dog', 'life', 'mammal']}
    assert r['violations'] == [['y', 'cat', 'dog']] and r['consistent'] is False


def test_unsatisfiable_class_without_members_is_consistent():
    r = oc([('d', 'a'), ('d', 'b')], [('b', 'a')], [])
    assert r['unsatisfiable'] == ['d'] and r['violations'] == [] and r['consistent'] is True
    r = oc([('d', 'a'), ('d', 'b')], [('b', 'a')], [('i', 'd')])
    assert r['violations'] == [['i', 'a', 'b']] and r['consistent'] is False
    assert r['unsatisfiable'] == ['d']


def test_empty_everything_and_disjoint_only():
    assert oc([], [], []) == {'classes': [], 'ancestors': {}, 'unsatisfiable': [], 'instance_types': {},
                              'violations': [], 'consistent': True}
    r = oc([], [('b', 'a')], [('i', 'a'), ('i', 'b')])
    assert r['violations'] == [['i', 'a', 'b']] and r['classes'] == ['a', 'b']


def test_individual_and_class_namespaces_are_separate():
    r = oc([('a', 'b')], [], [('a', 'a')])
    assert r['instance_types'] == {'a': ['a', 'b']} and r['consistent'] is True


def test_random_vs_oracle():
    rnd = random.Random(570)
    n_viol = n_unsat = 0
    for _ in range(400):
        names = ['c%d' % i for i in range(rnd.randint(1, 7))]
        subs = [(names[i], names[j]) for i in range(len(names)) for j in range(i + 1, len(names)) if rnd.random() < 0.3]
        rnd.shuffle(names)
        dis, seen = [], set()
        for _ in range(rnd.randint(0, 3)):
            a, b = rnd.sample(names, 2) if len(names) > 1 else (None, None)
            if a and (min(a, b), max(a, b)) not in seen:
                seen.add((min(a, b), max(a, b)))
                dis.append((a, b))
        inst = list({(rnd.choice('xyz'), rnd.choice(names)) for _ in range(rnd.randint(0, 5))})
        want = oracle(subs, dis, inst)
        got = oc(subs, dis, inst)
        assert got == want
        n_viol += bool(want['violations'])
        n_unsat += bool(want['unsatisfiable'])
    assert n_viol > 20 and n_unsat > 20


def err(f, exc, msg, *a):
    with pytest.raises(exc) as e:
        f(*a)
    assert str(e.value) == msg


NAME = 'must be 1 to 30 characters from A-Z, a-z, 0-9, _ and -'


def test_pins():
    err(oc, T, 'subclasses must be a list or tuple', 'ab', [], [])
    err(oc, T, 'disjoint must be a list or tuple', [], 'ab', [])
    err(oc, T, 'instances must be a list or tuple', [], [], 'ab')
    err(oc, V, 'subclasses count must be between 0 and 200', [('a%d' % i, 'b') for i in range(201)], [], [])
    err(oc, V, 'disjoint count must be between 0 and 100', [], [('a%d' % i, 'b') for i in range(101)], [])
    err(oc, V, 'instances count must be between 0 and 200', [], [], [('a%d' % i, 'b') for i in range(201)])
    for bad in ('ab', 5, None, ('a',), ('a', 'b', 'c'), {'a': 1, 'b': 2}):
        err(oc, T, 'each subclasses entry must be a pair', [('a', 'b'), bad], [], [])
        err(oc, T, 'each disjoint entry must be a pair', [], [bad], [])
        err(oc, T, 'each instances entry must be a pair', [], [], [bad])
    err(oc, T, 'child must be a str', [(1, 'b')], [], [])
    err(oc, T, 'parent must be a str', [('a', 1)], [], [])
    err(oc, T, 'class must be a str', [], [(1, 'b')], [])
    err(oc, T, 'class must be a str', [], [('a', None)], [])
    err(oc, T, 'individual must be a str', [], [], [(True, 'b')])
    err(oc, T, 'class must be a str', [], [], [('a', 2)])
    err(oc, V, 'child ' + NAME, [('', 'b')], [], [])
    err(oc, V, 'parent ' + NAME, [('a', 'b b')], [], [])
    err(oc, V, 'parent ' + NAME, [('a', 'x' * 31)], [], [])
    err(oc, V, 'class ' + NAME, [], [('a.', 'b')], [])
    err(oc, V, 'individual ' + NAME, [], [], [('', 'b')])
    err(oc, V, 'a subclasses pair cannot name the same class twice', [('a', 'a')], [], [])
    err(oc, V, 'a disjoint pair cannot name the same class twice', [], [('a', 'a')], [])
    err(oc, V, 'subclasses pairs must not repeat', [('a', 'b'), ('a', 'b')], [], [])
    err(oc, V, 'disjoint pairs must not repeat', [], [('a', 'b'), ('b', 'a')], [])
    err(oc, V, 'instances pairs must not repeat', [], [], [('i', 'a'), ('i', 'a')])
    err(oc, V, 'subclass pairs must be acyclic', [('a', 'b'), ('b', 'a')], [], [])
    err(oc, V, 'subclass pairs must be acyclic', [('a', 'b'), ('b', 'c'), ('c', 'a')], [], [])


def test_accepted_edges():
    oc([], [], [('i', 'a'), ('i', 'b')])                 # one individual in many classes
    oc([('x' * 30, 'A-z_9')], [], [])
    dag = [('c%d' % i, 'c%d' % j) for i in range(21) for j in range(i + 1, 21)]
    assert len(dag) == 210
    oc(dag[:200], [], [])                               # 200 subclasses
    err(oc, V, 'subclasses count must be between 0 and 200', dag[:201], [], [])
    comp = [('c%d' % i, 'c%d' % j) for i in range(15) for j in range(i + 1, 15)]
    assert len(comp) == 105
    oc([], comp[:100], [])                              # 100 disjoint
    err(oc, V, 'disjoint count must be between 0 and 100', [], comp[:101], [])
    oc([], [], [('i%d' % i, 'a') for i in range(200)])  # 200 instances
    oc([('c%d' % i, 'c%d' % (i + 1)) for i in range(59)], [], [])  # 60 classes
    err(oc, V, 'at most 60 classes are supported', [('c%d' % i, 'c%d' % (i + 1)) for i in range(60)], [], [])
    # a disjoint-only name, and an instance-only class, both count toward the cap
    err(oc, V, 'at most 60 classes are supported', [('c%d' % i, 'c%d' % (i + 1)) for i in range(59)], [('z1', 'z2')], [])
    err(oc, V, 'at most 60 classes are supported', [('c%d' % i, 'c%d' % (i + 1)) for i in range(59)], [], [('i', 'z1')])


def test_class_cap_is_checked_before_cycles_and_after_pairs():
    cyc = [('c%d' % i, 'c%d' % (i + 1)) for i in range(60)] + [('c60', 'c0')]
    err(oc, V, 'at most 60 classes are supported', cyc, [], [])
    err(oc, V, 'subclasses pairs must not repeat', [('a', 'b'), ('a', 'b')], [('z', 'z')], [])
    err(oc, V, 'a disjoint pair cannot name the same class twice', [('a', 'b'), ('b', 'a')], [('z', 'z')], [])


def test_every_position_validated():
    for pos in range(3):
        v = [('a', 'b'), ('c', 'd'), ('e', 'f')]
        v[pos] = ('a', 5)
        err(oc, T, 'parent must be a str', v, [], [])
        err(oc, T, 'class must be a str', [], v, [])
        err(oc, T, 'class must be a str', [], [], v)
        v[pos] = 5
        err(oc, T, 'each subclasses entry must be a pair', v, [], [])
        err(oc, T, 'each disjoint entry must be a pair', [], v, [])
        err(oc, T, 'each instances entry must be a pair', [], [], v)


def test_deep_chain_and_diamond_ancestors_unique():
    r = oc([('c%d' % i, 'c%d' % (i + 1)) for i in range(40)], [], [('i', 'c0')])
    assert r['ancestors']['c0'] == sorted('c%d' % i for i in range(1, 41))
    r = oc([('d', 'b'), ('d', 'c'), ('b', 'a'), ('c', 'a')], [], [('i', 'd')])
    assert r['ancestors']['d'] == ['a', 'b', 'c'] and r['instance_types']['i'] == ['a', 'b', 'c', 'd']


def test_dense_hierarchy_is_fast():
    # complete DAG over 20 classes has 2**19 distinct paths from the bottom class; ancestors must be shared, not re-walked
    import time
    dag = [('c%02d' % i, 'c%02d' % j) for i in range(20) for j in range(i + 1, 20)]
    t0 = time.time()
    r = oc(dag, [], [('i', 'c00')])
    assert time.time() - t0 < 3
    assert r['ancestors']['c00'] == ['c%02d' % j for j in range(1, 20)]
    assert r['instance_types']['i'] == ['c%02d' % j for j in range(20)]


def test_diamond_ladder_is_fast():
    # 29 layers of two classes, every class under both classes of the next layer: 2**28 paths, 58 classes, 112 pairs
    import time
    pairs = [('l%02d%s' % (i, x), 'l%02d%s' % (i + 1, y)) for i in range(28) for x in 'ab' for y in 'ab']
    t0 = time.time()
    r = oc(pairs, [], [('i', 'l00a')])
    assert time.time() - t0 < 3
    assert len(r['ancestors']['l00a']) == 56 and len(r['instance_types']['i']) == 57
