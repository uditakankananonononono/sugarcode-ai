"""Row570 hardening: exact-type subclass pins, full-message pins, closure
oracle, non-adjacent-order and mixed-validity witnesses, boundary accepts,
mutation sweep. Tests-only delta. No integer-typed slot exists (names are
strings), so int-subclass/IntEnum pins are N/A; a str subclass with lying
__eq__/__hash__ is pinned instead. Containers and pairs accept BOTH exact
list and exact tuple shape by design; subclasses of either are refused.
Two equivalent mutants found by the extended sweep and not killable by any
witness: parents[child] insertion order (ancestors accumulate into sets) and
sorted() on the unsatisfiable list (it iterates the already-sorted classes).
"""
import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import ontology_check as mod

SRC = pathlib.Path(mod.__file__).read_text()
T_, V_ = TypeError, ValueError


def _load_code(code):
    m = types.ModuleType('mutant')
    exec(code, m.__dict__)
    return m


def _raises(exc, message, fn, *args):
    with pytest.raises(exc) as info:
        fn(*args)
    assert str(info.value) == message


def _survives(battery, old, new):
    doc_end = SRC.index('"""', 3) + 3
    assert SRC.find(old) > doc_end, 'mutation target must be code, not the docstring'
    mutated = SRC.replace(old, new, 1)
    assert mutated != SRC
    code = compile(mutated, 'mutant', 'exec')  # a syntax error is not a kill
    def _timeout(*_):
        raise TimeoutError('mutant did not terminate')
    previous = signal.signal(signal.SIGALRM, _timeout)
    signal.alarm(5)
    try:
        battery(_load_code(code))
    except (Exception, pytest.fail.Exception):
        return False
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
    return True


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class WeirdStr(str):
    def __eq__(self, other):
        return True

    def __hash__(self):
        return 0


NAME = 'must be 1 to 30 characters from A-Z, a-z, 0-9, _ and -'


def _oracle(subs, dis, inst):
    names = sorted({x for p in subs for x in p} | {x for p in dis for x in p} | {c for _, c in inst})
    reach = {c: set() for c in names}
    for c, p in subs:
        reach[c].add(p)
    changed = True
    while changed:  # iterative closure, not the module's recursive memo
        changed = False
        for c in names:
            for p in list(reach[c]):
                if not reach[p] <= reach[c]:
                    reach[c] |= reach[p]
                    changed = True
    pairs = [tuple(sorted(p)) for p in dis]
    sat = lambda c, a: a == c or a in reach[c]
    unsat = sorted(c for c in names if any(sat(c, a) and sat(c, b) for a, b in pairs))
    types = {}
    for ind, c in inst:
        types.setdefault(ind, set()).add(c)
        types[ind] |= reach[c]
    viol = sorted([ind, a, b] for ind, t in types.items() for a, b in pairs if a in t and b in t)
    return {'classes': names, 'ancestors': {c: sorted(reach[c]) for c in names},
            'unsatisfiable': unsat,
            'instance_types': {i: sorted(types[i]) for i in sorted(types)},
            'violations': viol, 'consistent': not viol}


def _core(m):
    oc = m.check_ontology
    r = oc([('dog', 'mammal'), ('mammal', 'animal'), ('cat', 'mammal'), ('plant', 'life'), ('animal', 'life')],
           [('animal', 'plant'), ('dog', 'cat')], [('rex', 'dog'), ('x', 'plant'), ('y', 'cat'), ('y', 'dog')])
    assert r['violations'] == [['y', 'cat', 'dog']] and r['consistent'] is False
    assert r['ancestors']['cat'] == ['animal', 'life', 'mammal']
    # unsatisfiable class without members is consistent; with a member it violates
    r = oc([('d', 'a'), ('d', 'b')], [('b', 'a')], [])
    assert r['unsatisfiable'] == ['d'] and r['consistent'] is True
    r = oc([('d', 'a'), ('d', 'b')], [('b', 'a')], [('i', 'd')])
    assert r['violations'] == [['i', 'a', 'b']] and r['unsatisfiable'] == ['d']
    # empty everything; separate namespaces; instance self-name allowed
    assert oc([], [], [])['consistent'] is True
    assert oc([('a', 'b')], [], [('a', 'a')])['instance_types'] == {'a': ['a', 'b']}
    # violations sorted across individuals and pairs
    r = oc([], [('b', 'a'), ('d', 'c')], [('z', 'a'), ('z', 'b'), ('a1', 'c'), ('a1', 'd')])
    assert r['violations'] == [['a1', 'c', 'd'], ['z', 'a', 'b']]
    # tuple-shaped containers and pairs accepted
    assert oc((('a', 'b'),), (('c', 'd'),), (('i', 'a'),))['ancestors'] == {'a': ['b'], 'b': [], 'c': [], 'd': []}
    # boundary accepts
    oc([('x' * 30, 'A-z_9-0')], [], [])
    comp = [('c%d' % i, 'c%d' % j) for i in range(15) for j in range(i + 1, 15)]
    oc([], comp[:100], [])
    oc([('c%d' % i, 'c%d' % (i + 1)) for i in range(59)], [], [])
    oc([], [], [('i%d' % i, 'a') for i in range(200)])
    # seeded random oracle
    rng = random.Random(5701)
    for _ in range(150):
        names = ['c%d' % i for i in range(rng.randint(1, 7))]
        subs = [(names[i], names[j]) for i in range(len(names)) for j in range(i + 1, len(names))
                if rng.random() < 0.3]
        dis, seen = [], set()
        for _ in range(rng.randint(0, 3)):
            if len(names) > 1:
                a, b = rng.sample(names, 2)
                if (min(a, b), max(a, b)) not in seen:
                    seen.add((min(a, b), max(a, b)))
                    dis.append((a, b))
        inst = list({(rng.choice('xyz'), rng.choice(names)) for _ in range(rng.randint(0, 5))})
        assert oc(subs, dis, inst) == _oracle(subs, dis, inst)
    # dense shared-ancestor case (guards the ancestor memoization through the sweep alarm)
    pairs = [('l%02d%s' % (i, x), 'l%02d%s' % (i + 1, y)) for i in range(28) for x in 'ab' for y in 'ab']
    r = oc(pairs, [], [('i', 'l00a')])
    assert len(r['ancestors']['l00a']) == 56 and len(r['instance_types']['i']) == 57
    # full exact error messages
    _raises(T_, 'subclasses must be a list or tuple', oc, 'ab', [], [])
    _raises(T_, 'disjoint must be a list or tuple', oc, [], 'ab', [])
    _raises(T_, 'instances must be a list or tuple', oc, [], [], 'ab')
    _raises(V_, 'subclasses count must be between 0 and 200', oc, [('a%d' % i, 'b') for i in range(201)], [], [])
    _raises(V_, 'disjoint count must be between 0 and 100', oc, [], [('a%d' % i, 'b') for i in range(101)], [])
    _raises(V_, 'instances count must be between 0 and 200', oc, [], [], [('a%d' % i, 'b') for i in range(201)])
    _raises(T_, 'each subclasses entry must be a pair', oc, [('a',)], [], [])
    _raises(T_, 'each disjoint entry must be a pair', oc, [], [('a', 'b', 'c')], [])
    _raises(T_, 'each instances entry must be a pair', oc, [], [], [5])
    _raises(T_, 'child must be a str', oc, [(1, 'b')], [], [])
    _raises(T_, 'parent must be a str', oc, [('a', None)], [], [])
    _raises(T_, 'class must be a str', oc, [], [(True, 'b')], [])
    _raises(T_, 'individual must be a str', oc, [], [], [(1.0, 'b')])
    _raises(T_, 'class must be a str', oc, [], [], [('a', b'b')])
    _raises(V_, 'child ' + NAME, oc, [('', 'b')], [], [])
    _raises(V_, 'parent ' + NAME, oc, [('a', 'x' * 31)], [], [])
    _raises(V_, 'class ' + NAME, oc, [], [('a.', 'b')], [])
    _raises(V_, 'class ' + NAME, oc, [], [('a', 'b!')], [])
    _raises(V_, 'individual ' + NAME, oc, [], [], [('a b', 'b')])
    _raises(V_, 'a subclasses pair cannot name the same class twice', oc, [('a', 'a')], [], [])
    _raises(V_, 'a disjoint pair cannot name the same class twice', oc, [], [('a', 'a')], [])
    _raises(V_, 'subclasses pairs must not repeat', oc, [('a', 'b'), ('a', 'b')], [], [])
    _raises(V_, 'disjoint pairs must not repeat', oc, [], [('a', 'b'), ('b', 'a')], [])
    _raises(V_, 'instances pairs must not repeat', oc, [], [], [('i', 'a'), ('i', 'a')])
    _raises(V_, 'at most 60 classes are supported', oc, [('c%d' % i, 'c%d' % (i + 1)) for i in range(60)], [], [])
    _raises(V_, 'subclass pairs must be acyclic', oc, [('a', 'b'), ('b', 'a')], [], [])
    _raises(V_, 'subclass pairs must be acyclic', oc, [('a', 'b'), ('b', 'c'), ('c', 'a')], [], [])


def _mix(m):
    oc = m.check_ontology
    # non-adjacent repeats (positions 0 and 3), including unordered disjoint repeats
    _raises(V_, 'subclasses pairs must not repeat', oc, [('a', 'b'), ('c', 'd'), ('e', 'f'), ('a', 'b')], [], [])
    _raises(V_, 'disjoint pairs must not repeat', oc, [], [('a', 'b'), ('c', 'd'), ('b', 'a')], [])
    _raises(V_, 'instances pairs must not repeat', oc, [], [], [('i', 'a'), ('j', 'b'), ('i', 'a')])
    # non-adjacent invalid pairs among valid ones
    _raises(T_, 'parent must be a str', oc, [('a', 'b'), ('c', 'd'), ('e', 5)], [], [])
    _raises(V_, 'child ' + NAME, oc, [('a', 'b'), ('c', 'd'), ('e!', 'f')], [], [])
    # mixed-validity: subclass and bad values in later pairs after valid earlier pairs
    _raises(T_, 'each subclasses entry must be a pair', oc, [('a', 'b'), ('c', 'd'), T(('e', 'f'))], [], [])
    _raises(T_, 'each disjoint entry must be a pair', oc, [], [('a', 'b'), L(['c', 'd'])], [])
    _raises(T_, 'parent must be a str', oc, [('a', 'b'), ('c', S('d'))], [], [])
    _raises(T_, 'class must be a str', oc, [], [('a', 'b'), ('c', WeirdStr('d'))], [])
    _raises(T_, 'individual must be a str', oc, [], [], [('i', 'a'), (S('j'), 'b')])
    # ordering: pairs validated in order (subclasses, then disjoint, then instances),
    # then class cap, then acyclicity
    _raises(V_, 'subclasses pairs must not repeat', oc, [('a', 'b'), ('a', 'b')], [('z', 'z')], [])
    _raises(V_, 'a disjoint pair cannot name the same class twice', oc, [('a', 'b'), ('b', 'a')], [('z', 'z')], [])
    cyc = [('c%d' % i, 'c%d' % (i + 1)) for i in range(60)] + [('c60', 'c0')]
    _raises(V_, 'at most 60 classes are supported', oc, cyc, [], [])
    _raises(T_, 'class must be a str', oc,
            [('c%d' % i, 'c%d' % (i + 1)) for i in range(59)], [], [('i', 1)])


def _late(m):
    oc = m.check_ontology
    # container and pair subclasses refused with exact messages
    _raises(T_, 'subclasses must be a list or tuple', oc, L([('a', 'b')]), [], [])
    _raises(T_, 'subclasses must be a list or tuple', oc, T((('a', 'b'),)), [], [])
    _raises(T_, 'disjoint must be a list or tuple', oc, [], L([('a', 'b')]), [])
    _raises(T_, 'instances must be a list or tuple', oc, [], [], T((('i', 'a'),)))
    _raises(T_, 'each subclasses entry must be a pair', oc, [L(['a', 'b'])], [], [])
    _raises(T_, 'each subclasses entry must be a pair', oc, [T(('a', 'b'))], [], [])
    _raises(T_, 'child must be a str', oc, [(S('a'), 'b')], [], [])
    _raises(T_, 'class must be a str', oc, [], [(WeirdStr('a'), 'b')], [])
    # subclass refused before any cap
    _raises(T_, 'subclasses must be a list or tuple', oc, L([('a', 'b')] * 201), [], [])
    _raises(V_, 'subclasses count must be between 0 and 200', oc, [('a%d' % i, 'b') for i in range(201)], [], [])
    _raises(T_, 'child must be a str', oc, [(S('a' * 31), 'b')], [], [])
    # exact list-shaped and tuple-shaped acceptance counterparts
    assert oc(list([list(['a', 'b'])]), [], [])['classes'] == ['a', 'b']
    assert oc(tuple([tuple(('a', 'b'))]), [], [])['classes'] == ['a', 'b']
    assert oc([], [], [('i', 'a'), ('i', 'b')])['instance_types'] == {'i': ['a', 'b']}


def battery(m):
    _core(m)
    _mix(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ('type(v) is not str', 'not isinstance(v, str)'),
    ('type(vals) not in (list, tuple)', 'not isinstance(vals, (list, tuple))'),
    ('type(p) not in (list, tuple)', 'not isinstance(p, (list, tuple))'),
    ('MAX_SUB = 200', 'MAX_SUB = 201'),
    ('MAX_DISJOINT = 100', 'MAX_DISJOINT = 101'),
    ('MAX_INST = 200', 'MAX_INST = 201'),
    ('MAX_CLASSES = 60', 'MAX_CLASSES = 61'),
    ('not 1 <= len(v) <= 30', 'not 1 <= len(v) <= 31'),
    ('not 1 <= len(v) <= 30', 'not 2 <= len(v) <= 30'),
    ("frozenset('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-')",
     "frozenset('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_')"),
    ("if what != 'instances' and a == b", 'if a == b'),
    ("if what != 'instances' and a == b", 'if False'),
    ('key = tuple(sorted((a, b))) if unordered else (a, b)', 'key = (a, b)'),
    ('if key in seen', 'if False'),
    ('got |= up(p)', 'pass'),
    ('        if state.get(c) == 2:\n            return anc[c]', '        if False:\n            return anc[c]'),
    ('if state.get(c) == 1', 'if state.get(c) == 3'),
    ('a in anc[c] | {c} and b in anc[c] | {c}', 'a in anc[c] | {c} or b in anc[c] | {c}'),
    ('pairs = [tuple(sorted(p)) for p in dis]', 'pairs = [tuple(p) for p in dis]'),
    ('viol = sorted(', 'viol = list('),
    ("'consistent': not viol", "'consistent': True"),
    ('classes = sorted(', 'classes = list('),
    ('types.setdefault(ind, set()).update(anc[c] | {c})', 'types.setdefault(ind, set()).update(anc[c])'),
    ("' must be a list or tuple'", "' must be a list'"),
    ("' entry must be a pair'", "' entry must be pair'"),
    ("' pairs must not repeat'", "' pairs must not repeat.'"),
    ("'at most 60 classes are supported'", "'at most sixty classes are supported'"),
    ("'subclass pairs must be acyclic'", "'subclass pairs must not have cycles'"),
    ("' count must be between 0 and %d'", "' count must be at most %d'"),
    ("' pair cannot name the same class twice'", "' pair cannot name the same class 2x'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
