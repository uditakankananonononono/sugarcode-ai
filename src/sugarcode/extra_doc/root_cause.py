"""Row 463, Root Cause Analysis: exact structure of a cause-and-effect graph around one failure.

analyse_causes(edges, failure) takes edges, each a (cause, effect) pair of node names, and the name of the failure.
It returns, exactly and in a fixed order:
  ancestors   every node with a causal path to the failure (the failure itself excluded), sorted;
  roots       the ancestors that have no cause in the graph at all, sorted;
  chains      every simple causal chain from a root to the failure, as lists of names, sorted;
  chain_count their number;
  min_cut     the smallest set of nodes (any ancestor, never the failure) whose removal leaves no root able to reach
              the failure, as a sorted list; among equally small sets the one that sorts first is returned;
  min_cut_size its length.
A failure with no causes gives empty lists and size 0.
Caps: 1 to 200 edges, as a list or tuple of 2-element lists or tuples; node names are str of 1 to 30 characters from
A-Z, a-z, 0-9, '_' and '-'; no self-loop and no repeated edge; the whole graph must be acyclic; the failure must
appear in some edge; at most 12 ancestors (the cut is found by trying every subset) and at most 1000 chains.
Order of checks: edges type, edge count, then each edge in order (pair shape, str types, names, self-loop, repeat),
then failure type and name, failure present, acyclic, ancestor cap, chain cap, and only then the result is built.

NOT_CLAIMED: graph arithmetic only. It does not say that any listed edge is a real cause, that the graph is complete,
that a root is the root cause in the sense of the true origin, that removing the cut nodes would prevent the failure
in practice, or that the cut is the cheapest fix; the graph is whatever the caller supplies. No clinical or wet-lab
claim.
"""
from itertools import combinations

MAX_EDGES = 200
MAX_ANCESTORS = 12
MAX_CHAINS = 1000
NAME_CHARS = frozenset('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-')


def _name(v, what):
    if type(v) is not str:
        raise TypeError(what + ' must be a str')
    if not 1 <= len(v) <= 30 or any(ch not in NAME_CHARS for ch in v):
        raise ValueError(what + ' must be 1 to 30 characters from A-Z, a-z, 0-9, _ and -')
    return v


def analyse_causes(edges, failure):
    if type(edges) not in (list, tuple):
        raise TypeError('edges must be a list or tuple')
    if not 1 <= len(edges) <= MAX_EDGES:
        raise ValueError('edge count must be between 1 and 200')
    seen = set()
    for e in edges:
        if type(e) not in (list, tuple) or len(e) != 2:
            raise TypeError('each edge must be a (cause, effect) pair')
        a = _name(e[0], 'cause')
        b = _name(e[1], 'effect')
        if a == b:
            raise ValueError('an edge cannot join a node to itself')
        if (a, b) in seen:
            raise ValueError('edges must not repeat')
        seen.add((a, b))
    f = _name(failure, 'failure')
    nodes = {x for e in seen for x in e}
    if f not in nodes:
        raise ValueError('failure must appear in an edge')
    succ = {x: [] for x in nodes}
    pred = {x: [] for x in nodes}
    for a, b in sorted(seen):
        succ[a].append(b)
        pred[b].append(a)
    indeg = {x: len(pred[x]) for x in nodes}
    todo = [x for x in nodes if indeg[x] == 0]
    done = 0
    while todo:
        x = todo.pop()
        done += 1
        for y in succ[x]:
            indeg[y] -= 1
            if indeg[y] == 0:
                todo.append(y)
    if done != len(nodes):
        raise ValueError('edges must form an acyclic graph')
    anc, stack = set(), [f]
    while stack:
        x = stack.pop()
        for p in pred[x]:
            if p not in anc:
                anc.add(p)
                stack.append(p)
    if len(anc) > MAX_ANCESTORS:
        raise ValueError('at most 12 ancestors are supported')
    roots = sorted(x for x in anc if not pred[x])
    chains = []

    def walk(x, path):
        if len(chains) > MAX_CHAINS:
            return
        if x == f:
            chains.append(path)
            return
        for y in succ[x]:
            if y == f or y in anc:
                walk(y, path + [y])
    for r in roots:
        walk(r, [r])
    if len(chains) > MAX_CHAINS:
        raise ValueError('too many causal chains')
    chains.sort()
    ancs = sorted(anc)

    def blocked(cut):
        seen2 = set()
        st = [r for r in roots if r not in cut]
        seen2.update(st)
        while st:
            x = st.pop()
            if x == f:
                return False
            for y in succ[x]:
                if y not in cut and y not in seen2:
                    seen2.add(y)
                    st.append(y)
        return True
    cut = []
    for k in range(len(ancs) + 1):
        hit = [c for c in combinations(ancs, k) if blocked(set(c))]
        if hit:
            cut = list(hit[0])
            break
    return {'ancestors': ancs, 'roots': roots, 'chains': chains, 'chain_count': len(chains),
            'min_cut': cut, 'min_cut_size': len(cut)}
