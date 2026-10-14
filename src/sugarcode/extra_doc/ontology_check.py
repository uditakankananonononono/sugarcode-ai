"""Row 570, Ontology Design: exact consistency check of a small class hierarchy.

check_ontology(subclasses, disjoint, instances) takes
  subclasses  (child, parent) pairs: every child is a kind of its parent;
  disjoint    (a, b) pairs: nothing can be both a and b;
  instances   (individual, class) pairs: the individual is asserted to belong to the class.
It returns, exactly and in a fixed order:
  classes        every class name that appears anywhere, sorted;
  ancestors      for each class, its strict ancestors through the subclass pairs, sorted;
  unsatisfiable  classes that are (through themselves and their ancestors) inside both sides of a disjoint pair, sorted;
  instance_types for each individual, every class it belongs to once ancestors are added, sorted;
  violations     [individual, a, b] for each individual whose types include both sides of a disjoint pair (a, b are
                 the pair's names in sorted order), sorted;
  consistent     True when there are no violations (an unsatisfiable class with no members is not a violation).
Caps: each of the three arguments a list or tuple; subclasses 0 to 200 pairs, disjoint 0 to 100, instances 0 to 200;
names are str of 1 to 30 characters from A-Z, a-z, 0-9, '_' and '-' (individuals and classes are separate
namespaces); no self-pair; no repeated subclass pair, repeated instance pair or repeated disjoint pair (a, b equals
b, a); at most 60 classes; the subclass pairs must be acyclic.
Order of checks: subclasses (type, count, then each pair in order: shape, types, names, self-pair, repeat), then
disjoint, then instances the same way, then the class cap, then acyclicity, and only then the result is built.

NOT_CLAIMED: structural bookkeeping only. It does not say the hierarchy models the real concepts, that the disjoint
pairs are true, that missing links are absent in reality, or that the ontology is complete or useful; no reasoning
beyond subclass closure and disjointness is done. No clinical or wet-lab claim.
"""

MAX_SUB = 200
MAX_DISJOINT = 100
MAX_INST = 200
MAX_CLASSES = 60
NAME_CHARS = frozenset('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-')


def _name(v, what):
    if type(v) is not str:
        raise TypeError(what + ' must be a str')
    if not 1 <= len(v) <= 30 or any(ch not in NAME_CHARS for ch in v):
        raise ValueError(what + ' must be 1 to 30 characters from A-Z, a-z, 0-9, _ and -')
    return v


def _pairs(vals, what, limit, first, second, unordered=False):
    if type(vals) not in (list, tuple):
        raise TypeError(what + ' must be a list or tuple')
    if not 0 <= len(vals) <= limit:
        raise ValueError(what + ' count must be between 0 and %d' % limit)
    out, seen = [], set()
    for p in vals:
        if type(p) not in (list, tuple) or len(p) != 2:
            raise TypeError('each ' + what + ' entry must be a pair')
        a = _name(p[0], first)
        b = _name(p[1], second)
        if what != 'instances' and a == b:
            raise ValueError('a ' + what + ' pair cannot name the same class twice')
        key = tuple(sorted((a, b))) if unordered else (a, b)
        if key in seen:
            raise ValueError(what + ' pairs must not repeat')
        seen.add(key)
        out.append((a, b))
    return out


def check_ontology(subclasses, disjoint, instances):
    subs = _pairs(subclasses, 'subclasses', MAX_SUB, 'child', 'parent')
    dis = _pairs(disjoint, 'disjoint', MAX_DISJOINT, 'class', 'class', unordered=True)
    inst = _pairs(instances, 'instances', MAX_INST, 'individual', 'class')
    classes = sorted({x for p in subs for x in p} | {x for p in dis for x in p} | {c for _, c in inst})
    if len(classes) > MAX_CLASSES:
        raise ValueError('at most 60 classes are supported')
    parents = {c: [] for c in classes}
    for child, parent in subs:
        parents[child].append(parent)
    anc = {}
    state = {}

    def up(c):
        if state.get(c) == 1:
            raise ValueError('subclass pairs must be acyclic')
        if state.get(c) == 2:
            return anc[c]
        state[c] = 1
        got = set()
        for p in parents[c]:
            got.add(p)
            got |= up(p)
        state[c] = 2
        anc[c] = got
        return got
    for c in classes:
        up(c)
    pairs = [tuple(sorted(p)) for p in dis]
    unsat = sorted(c for c in classes if any(a in anc[c] | {c} and b in anc[c] | {c} for a, b in pairs))
    types = {}
    for ind, c in inst:
        types.setdefault(ind, set()).update(anc[c] | {c})
    viol = sorted([ind, a, b] for ind, t in types.items() for a, b in pairs if a in t and b in t)
    return {'classes': classes,
            'ancestors': {c: sorted(anc[c]) for c in classes},
            'unsatisfiable': unsat,
            'instance_types': {i: sorted(types[i]) for i in sorted(types)},
            'violations': viol,
            'consistent': not viol}
