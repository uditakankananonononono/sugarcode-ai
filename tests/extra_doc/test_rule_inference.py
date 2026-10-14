import random
import pytest
from sugarcode.extra_doc.rule_inference import forward_chain as fc

T, V = TypeError, ValueError


def oracle(facts, rules):
    # label-correcting depth: depth[x] = 0 for facts, else 1 + max depth of a rule's premises, smallest over rules
    INF = 10 ** 9
    names = set(facts) | {c for _, c in rules} | {p for ps, _ in rules for p in ps}
    depth = {x: (0 if x in facts else INF) for x in names}
    changed = True
    while changed:
        changed = False
        for ps, c in rules:
            d = 1 + max([depth[p] for p in ps], default=0)
            if d < depth[c] and max([depth[p] for p in ps], default=0) < INF:
                depth[c] = d
                changed = True
    out = []
    for x in sorted(names):
        if 0 < depth[x] < INF:
            first = min(i for i, (ps, c) in enumerate(rules)
                        if c == x and max([depth[p] for p in ps], default=0) == depth[x] - 1)
            out.append([x, depth[x], first])
    out.sort(key=lambda d: (d[1], d[0]))
    top = max([d[1] for d in out], default=0)
    return {'facts': sorted(x for x in names if depth[x] < INF), 'derived': out, 'rounds': top}


def test_hand_cases():
    r = fc(['a'], [(['a'], 'b'), (['b', 'a'], 'c'), (['c'], 'd'), (['x'], 'y')])
    assert r == {'facts': ['a', 'b', 'c', 'd'], 'derived': [['b', 1, 0], ['c', 2, 1], ['d', 3, 2]], 'rounds': 3}
    # premise-free rule fires in round 1; two rules for one name: lowest index wins
    r = fc([], [([], 'p'), (['p'], 'q'), (['p'], 'q'), ([], 'q')])
    assert r['derived'] == [['p', 1, 0], ['q', 1, 3]] and r['rounds'] == 1
    assert r['facts'] == ['p', 'q']


def test_round_semantics_are_parallel_not_sequential():
    # b and c are both derived in round 1 from a; d needs both so it comes in round 2 even if listed first
    r = fc(['a'], [(['b', 'c'], 'd'), (['a'], 'b'), (['a'], 'c')])
    assert r['derived'] == [['b', 1, 1], ['c', 1, 2], ['d', 2, 0]] and r['rounds'] == 2


def test_nothing_derived_and_known_conclusions_skipped():
    assert fc(['a'], []) == {'facts': ['a'], 'derived': [], 'rounds': 0}
    assert fc([], []) == {'facts': [], 'derived': [], 'rounds': 0}
    r = fc(['a', 'b'], [(['a'], 'b')])
    assert r == {'facts': ['a', 'b'], 'derived': [], 'rounds': 0}
    r = fc(['a'], [(['a', 'z'], 'b')])
    assert r['derived'] == [] and r['facts'] == ['a']
    r = fc(['a'], [(['a'], 'a')])
    assert r['derived'] == []


def test_cycles_terminate():
    r = fc(['a'], [(['a'], 'b'), (['b'], 'a'), (['b'], 'c'), (['c'], 'b')])
    assert r['facts'] == ['a', 'b', 'c'] and r['rounds'] == 2


def test_random_vs_oracle():
    rnd = random.Random(571)
    deep = 0
    for _ in range(500):
        names = ['n%d' % i for i in range(rnd.randint(1, 9))]
        facts = rnd.sample(names, rnd.randint(0, min(3, len(names))))
        rules = [(rnd.sample(names, rnd.randint(0, min(3, len(names)))), rnd.choice(names)) for _ in range(rnd.randint(0, 10))]
        want = oracle(set(facts), rules)
        got = fc(facts, rules)
        assert got == want
        deep += want['rounds'] >= 3
    assert deep > 5


def test_long_chain_hits_100_names():
    rules = [(['c%d' % i], 'c%d' % (i + 1)) for i in range(99)]
    r = fc(['c0'], rules)
    assert r['rounds'] == 99 and r['derived'][-1] == ['c99', 99, 98] and len(r['facts']) == 100


def err(f, exc, msg, *a):
    with pytest.raises(exc) as e:
        f(*a)
    assert str(e.value) == msg


NAME = 'must be 1 to 30 characters from A-Z, a-z, 0-9, _ and -'


def test_pins():
    err(fc, T, 'facts must be a list or tuple', 'ab', [])
    err(fc, T, 'facts must be a list or tuple', {'a'}, [])
    err(fc, V, 'fact count must be between 0 and 100', ['f%d' % i for i in range(101)], [])
    err(fc, T, 'fact must be a str', [1], [])
    err(fc, T, 'fact must be a str', [True], [])
    err(fc, V, 'fact ' + NAME, [''], [])
    err(fc, V, 'fact ' + NAME, ['a b'], [])
    err(fc, V, 'fact ' + NAME, ['x' * 31], [])
    err(fc, V, 'facts must not repeat', ['a', 'a'], [])
    err(fc, T, 'rules must be a list or tuple', [], 'ab')
    err(fc, V, 'rule count must be between 0 and 100', [], [([], 'r%d' % i) for i in range(101)])
    for bad in ('ab', 5, None, (['a'],), (['a'], 'b', 'c'), {'a': 1, 'b': 2}):
        err(fc, T, 'each rule must be a (premises, conclusion) pair', [], [([], 'a'), bad])
    err(fc, T, 'premises must be a list or tuple', [], [('a', 'b')])
    err(fc, T, 'premises must be a list or tuple', [], [(None, 'b')])
    err(fc, V, 'premise count must be between 0 and 8', [], [(['p%d' % i for i in range(9)], 'b')])
    err(fc, T, 'premise must be a str', [], [([1], 'b')])
    err(fc, V, 'premise ' + NAME, [], [(['a b'], 'b')])
    err(fc, V, 'premises must not repeat', [], [(['a', 'a'], 'b')])
    err(fc, T, 'conclusion must be a str', [], [(['a'], 1)])
    err(fc, V, 'conclusion ' + NAME, [], [(['a'], '')])


def test_caps_accepted_and_refused():
    fc(['f%d' % i for i in range(100)], [])
    fc([], [(['p%d' % i for i in range(8)], 'q')])
    fc([], [([], 'r%d' % i) for i in range(100)])
    fc(['x' * 30], [(['A-z_9'], 'k')])
    err(fc, V, 'at most 100 distinct names are supported', ['f%d' % i for i in range(100)], [(['f0'], 'extra')])
    err(fc, V, 'at most 100 distinct names are supported', ['f%d' % i for i in range(100)], [(['extra'], 'f0')])
    rr = [([], 'r%d' % i) for i in range(99)] + [(['zz'], 'r0')]
    fc([], rr)
    err(fc, V, 'at most 100 distinct names are supported', ['q'], rr)


def test_check_order_and_every_position():
    err(fc, V, 'facts must not repeat', ['a', 'a'], 'bad')
    err(fc, T, 'rules must be a list or tuple', ['a'], 'bad')
    err(fc, T, 'each rule must be a (premises, conclusion) pair', [], [(['a'], 'b'), 5, (['a', 'a'], 'c')])
    err(fc, V, 'premises must not repeat', [], [(['a', 'a'], 'b'), (['a'], 1)])
    for pos in range(3):
        rules = [(['a'], 'b'), (['c'], 'd'), (['e'], 'f')]
        rules[pos] = (['a'], 5)
        err(fc, T, 'conclusion must be a str', [], rules)
        rules[pos] = ([5], 'b')
        err(fc, T, 'premise must be a str', [], rules)
        rules[pos] = 5
        err(fc, T, 'each rule must be a (premises, conclusion) pair', [], rules)
        facts = ['a', 'b', 'c']
        facts[pos] = 5
        err(fc, T, 'fact must be a str', facts, [])
