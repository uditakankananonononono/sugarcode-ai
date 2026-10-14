import random
from itertools import product
import pytest
import sugarcode.extra_doc.interactive_fiction as m
from sugarcode.extra_doc.interactive_fiction import analyse_story, branching_skeleton


def oracle(story, start):
    nodes = list(story)
    idx = {n: i for i, n in enumerate(nodes)}
    N = len(nodes)
    R = [[False] * N for _ in range(N)]  # path of length >= 1
    for u in nodes:
        for _, v in story[u]:
            R[idx[u]][idx[v]] = True
    for k, i, j in product(range(N), repeat=3):
        if R[i][k] and R[k][j]:
            R[i][j] = True
    s = idx[start]
    reach = sorted(n for n in nodes if n == start or R[s][idx[n]])
    endings = sorted(n for n in reach if not story[n])
    # distances by repeated relaxation
    INF = 10 ** 9
    d = {n: INF for n in nodes}
    d[start] = 0
    for _ in range(N):
        for u in nodes:
            for _, v in story[u]:
                d[v] = min(d[v], d[u] + 1)
    good = all(any(not story[e] and (e == n or R[idx[n]][idx[e]]) for e in nodes) for n in reach)
    cyc = any(R[idx[n]][idx[n]] for n in reach)
    # simple paths by explicit enumeration of walks as lists
    paths, calls = 0, 0
    stack = [[start]]
    while stack:
        w = stack.pop()
        calls += 1
        last = w[-1]
        if not story[last]:
            paths += 1
        for _, v in story[last]:
            if v not in w:
                stack.append(w + [v])
    return dict(reachable=reach, unreachable=sorted(set(nodes) - set(reach)), endings=endings,
                dead_end_free=good, has_cycle=cyc, depth={n: d[n] for n in reach},
                shortest_to_ending=min((d[e] for e in endings), default=None), simple_paths=paths), calls


def test_random_graphs_vs_oracle():
    rnd = random.Random(5)
    for _ in range(400):
        n = rnd.randint(1, 8)
        ids = ['s%d' % i for i in range(n)]
        story = {i: [('go %d' % j, rnd.choice(ids)) for j in range(rnd.choice([0, 0, 1, 2, 3]))] for i in ids}
        start = rnd.choice(ids)
        exp, _ = oracle(story, start)
        assert analyse_story(story, start) == exp


def test_hand_cases():
    r = analyse_story({'a': [('x', 'b'), ('y', 'c')], 'b': [('z', 'c')], 'c': [], 'z': []}, 'a')
    assert r['reachable'] == ['a', 'b', 'c'] and r['unreachable'] == ['z']
    assert r['endings'] == ['c'] and r['simple_paths'] == 2 and r['shortest_to_ending'] == 1
    assert r['dead_end_free'] is True and r['has_cycle'] is False and r['depth'] == {'a': 0, 'b': 1, 'c': 1}
    r = analyse_story({'a': [('x', 'a')]}, 'a')
    assert r['has_cycle'] is True and r['endings'] == [] and r['dead_end_free'] is False
    assert r['shortest_to_ending'] is None and r['simple_paths'] == 0
    r = analyse_story({'a': [('x', 'b'), ('t', 'e')], 'b': [('x', 'b')], 'e': []}, 'a')
    assert r['dead_end_free'] is False and r['has_cycle'] is True and r['simple_paths'] == 1
    r = analyse_story({'a': [('x', 'b')], 'b': [('y', 'a'), ('z', 'e')], 'e': []}, 'a')
    assert r['has_cycle'] is True and r['dead_end_free'] is True and r['simple_paths'] == 1
    r = analyse_story({'only': []}, 'only')
    assert r['endings'] == ['only'] and r['shortest_to_ending'] == 0 and r['simple_paths'] == 1
    # a trap loop that is unreachable does not make the story trapped
    r = analyse_story({'a': [], 'b': [('x', 'b')]}, 'a')
    assert r['dead_end_free'] is True and r['has_cycle'] is False and r['unreachable'] == ['b']


def test_skeleton_counts():
    for depth in range(5):
        for br in (1, 2, 3):
            total = sum(br ** d for d in range(depth + 1))
            if total > 30:
                with pytest.raises(ValueError) as e:
                    branching_skeleton(depth, br)
                assert str(e.value) == 'skeleton would exceed 30 nodes'
                continue
            r = branching_skeleton(depth, br)
            a = r['analysis']
            assert len(r['story']) == total and r['start'] == 'n0'
            assert len(a['endings']) == br ** depth and a['simple_paths'] == br ** depth
            assert a['shortest_to_ending'] == depth and a['has_cycle'] is False
            assert a['dead_end_free'] is True and a['unreachable'] == []
            assert a['depth'] == oracle(r['story'], 'n0')[0]['depth']
            assert a == oracle(r['story'], 'n0')[0]
    r = branching_skeleton(2, 2)
    assert r['story'] == {'n0': [('choice 1', 'n1'), ('choice 2', 'n2')],
                          'n1': [('choice 1', 'n3'), ('choice 2', 'n4')],
                          'n2': [('choice 1', 'n5'), ('choice 2', 'n6')],
                          'n3': [], 'n4': [], 'n5': [], 'n6': []}
    assert branching_skeleton(0, 3)['story'] == {'n0': []}


def test_path_cap_exact(monkeypatch):
    story = {'a': [('1', 'b'), ('2', 'c')], 'b': [('3', 'c')], 'c': []}
    _, calls = oracle(story, 'a')
    monkeypatch.setattr(m, 'MAX_WALK', calls)
    assert analyse_story(story, 'a')['simple_paths'] == 2
    monkeypatch.setattr(m, 'MAX_WALK', calls - 1)
    with pytest.raises(ValueError) as e:
        analyse_story(story, 'a')
    assert str(e.value) == 'path search too large'


def test_pathological_graph_hits_real_cap():
    ids = ['n%d' % i for i in range(30)]
    story = {ids[i]: [('c%d' % j, ids[i + 1 + j]) for j in range(6) if i + 1 + j < 30] for i in range(30)}
    with pytest.raises(ValueError) as e:
        analyse_story(story, 'n0')
    assert str(e.value) == 'path search too large'
    assert m.MAX_WALK == 100000


def err(exc, msg, *a):
    with pytest.raises(exc) as e:
        analyse_story(*a)
    assert str(e.value) == msg


def test_pins():
    T, V = TypeError, ValueError
    err(T, 'story must be a dict', [('a', [])], 'a')
    err(V, 'node count must be between 1 and 30', {}, 'a')
    err(V, 'node count must be between 1 and 30', {'n%d' % i: [] for i in range(31)}, 'n0')
    analyse_story({'n%d' % i: [] for i in range(30)}, 'n0')
    err(T, 'node id must be str', {1: []}, 'a')
    err(V, 'node id must be 1 to 20 printable ASCII characters', {'': []}, 'a')
    err(V, 'node id must be 1 to 20 printable ASCII characters', {'x' * 21: []}, 'a')
    analyse_story({'x' * 20: []}, 'x' * 20)
    err(V, 'node id must be 1 to 20 printable ASCII characters', {'a\n': []}, 'a')
    err(V, 'node id must be 1 to 20 printable ASCII characters', {'\u00e9': []}, 'a')
    err(T, 'choices must be a list or tuple of (label, target) pairs', {'a': 'x'}, 'a')
    err(V, 'at most 6 choices per node', {'a': [('l', 'a')] * 7}, 'a')
    analyse_story({'a': [('l', 'a')] * 6}, 'a')
    err(T, 'choices must be a list or tuple of (label, target) pairs', {'a': ['ab']}, 'a')
    err(T, 'choices must be a list or tuple of (label, target) pairs', {'a': [('l', 'a', 'a')]}, 'a')
    err(T, 'choice label must be str', {'a': [(1, 'a')]}, 'a')
    err(V, 'choice label must be 1 to 60 printable ASCII characters', {'a': [('', 'a')]}, 'a')
    err(V, 'choice label must be 1 to 60 printable ASCII characters', {'a': [('x' * 61, 'a')]}, 'a')
    analyse_story({'a': [('x' * 60, 'a')]}, 'a')
    err(V, 'choice label must be 1 to 60 printable ASCII characters', {'a': [('\t', 'a')]}, 'a')
    err(T, 'choice target must be str', {'a': [('l', None)]}, 'a')
    err(T, 'choice target must be str', {'a': [('l', ['a'])]}, 'a')
    err(T, 'start must be str', {'a': []}, 1)
    err(V, 'start is not a node', {'a': []}, 'b')
    err(V, 'choice target is not a node', {'a': [('l', 'zz')]}, 'a')
    err(V, 'choice target is not a node', {'a': [], 'b': [('l', 'zz')]}, 'a')  # unreachable node still validated
    err(T, 'story must be a dict', None, 'a')


def test_validation_even_when_cap_or_empty():
    # a bad value in the last node is still found when the first node would be fine
    for pos in range(4):
        story = {'n%d' % i: [] for i in range(4)}
        story['n%d' % pos] = [('x', 3)]
        err(TypeError, 'choice target must be str', story, 'n0')


def test_skeleton_pins():
    def e(exc, msg, *a):
        with pytest.raises(exc) as x:
            branching_skeleton(*a)
        assert str(x.value) == msg
    for bad in (True, 1.0, '1', None):
        e(TypeError, 'depth and branching must be nonbool ints', bad, 1)
        e(TypeError, 'depth and branching must be nonbool ints', 1, bad)
    e(ValueError, 'depth must be between 0 and 4', -1, 1)
    e(ValueError, 'depth must be between 0 and 4', 5, 1)
    e(ValueError, 'branching must be between 1 and 3', 1, 0)
    e(ValueError, 'branching must be between 1 and 3', 1, 4)
    e(ValueError, 'skeleton would exceed 30 nodes', 4, 3)
    assert len(branching_skeleton(4, 1)['story']) == 5
    e(ValueError, 'skeleton would exceed 30 nodes', 4, 2)  # 31 nodes
    assert len(branching_skeleton(3, 2)['story']) == 15


def test_gap_closers():
    err(TypeError, 'choices must be a list or tuple of (label, target) pairs', {'a': ''}, 'a')
    err(TypeError, 'choices must be a list or tuple of (label, target) pairs', {'a': 'ab'}, 'a')
    analyse_story({'~ !': []}, '~ !')
    for bad in ('\x1f', '\x7f', '\u00e9'):
        err(ValueError, 'node id must be 1 to 20 printable ASCII characters', {'a' + bad: []}, 'a')
        err(ValueError, 'choice label must be 1 to 60 printable ASCII characters', {'a': [('l' + bad, 'a')]}, 'a')


def test_parallel_choices_count_as_two_paths():
    r = analyse_story({'a': [('x', 'b'), ('y', 'b')], 'b': []}, 'a')
    assert r['simple_paths'] == 2 == oracle({'a': [('x', 'b'), ('y', 'b')], 'b': []}, 'a')[0]['simple_paths']
