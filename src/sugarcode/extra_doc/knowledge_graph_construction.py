"""Knowledge Graph Construction - exact relation graph with rule closure over caller triples.

Pure function over caller data. No retrieval, no network, no clock, no floats, no
randomness. Input: triples, 1..100 [subject, predicate, object] strings of 1..30
characters from a-z, 0-9 and underscore; rules, 0..10 [predicate, kind, other] entries
where kind is "symmetric" or "transitive" (other must be None) or "inverse" (other is a
different predicate name). At most 40 distinct nodes (subjects and objects) are accepted.

Method: the stated triples (duplicates collapsed) are closed under the rules until a
fixpoint, all in exact set arithmetic. Symmetric p: (a p b) gives (b p a). Inverse p/q:
(a p b) gives (b q a) and (a q b) gives (b p a). Transitive p: (a p b) and (b p c) give
(a p c). The closure is refused if it would exceed 5000 edges. The result lists nodes,
every edge marked stated or inferred, per-node out and in degree over all edges, and
the number of weakly connected components over all edges (every node counts, isolated
ones are not possible because every node is in some triple).

Scope: bounded for the Knowledge Graph Construction line. An exact in-memory graph with
three rule types over the caller's own triples. It is not an ontology reasoner: no
class hierarchies, no property chains, no entity resolution, no extraction from text.

Not claimed: that a stated or inferred edge is true of the world, that the rules are
valid for the predicates they name, that the graph is complete, or anything about the
real world. Every claim flag in the result is False.
"""
MAX_TRIPLES = 100
MAX_RULES = 10
MAX_NAME = 30
MAX_NODES = 40
MAX_EDGES = 5000
KINDS = ("symmetric", "transitive", "inverse")
_TOP = frozenset({"triples", "rules"})

NOT_CLAIMED = (
    "a stated or inferred edge is true of the world",
    "the rules are valid for the predicates they name",
    "the graph is complete",
    "real-world outcome",
)
CLAIMS = {"truth": False, "rules_valid": False, "complete": False, "real_world": False}


class KgError(ValueError):
    pass


def _name_ok(s):
    return 1 <= len(s) <= MAX_NAME and all(("a" <= c <= "z") or ("0" <= c <= "9") or c == "_" for c in s)


def _name(v, what):
    if not isinstance(v, str):
        raise KgError(f"{what} must be a string")
    if not _name_ok(v):
        raise KgError("name must be 1..30 characters from a-z, 0-9 and underscore")
    return v


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise KgError("data keys must be exactly triples, rules")
    raw = data["triples"]
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_TRIPLES:
        raise KgError("triples must be a list of 1..100 [subject, predicate, object]")
    edges, nodes = set(), set()
    for t in raw:
        if not isinstance(t, list) or len(t) != 3:
            raise KgError("triple must be [subject, predicate, object]")
        s, p, o = _name(t[0], "subject"), _name(t[1], "predicate"), _name(t[2], "object")
        nodes.update((s, o))
        edges.add((s, p, o))
    if len(nodes) > MAX_NODES:
        raise KgError("too many distinct nodes")
    rr = data["rules"]
    if not isinstance(rr, list) or len(rr) > MAX_RULES:
        raise KgError("rules must be a list of 0..10 rules")
    rules, seen = [], set()
    for r in rr:
        if not isinstance(r, list) or len(r) != 3:
            raise KgError("rule must be [predicate, kind, other]")
        p, kind, other = _name(r[0], "rule predicate"), r[1], r[2]
        if not isinstance(kind, str) or kind not in KINDS:
            raise KgError("rule kind must be symmetric, transitive or inverse")
        if kind == "inverse":
            other = _name(other, "inverse predicate")
            if other == p:
                raise KgError("inverse predicate must differ from the rule predicate")
        elif other is not None:
            raise KgError("other must be None unless kind is inverse")
        if (p, kind, other) in seen:
            raise KgError("rules must be distinct")
        seen.add((p, kind, other))
        rules.append((p, kind, other))
    return edges, rules


def knowledge_graph_construction(data):
    stated, rules = _validate(data)
    edges = set(stated)
    changed = True
    while changed:
        changed = False
        new = set()
        for p, kind, other in rules:
            if kind == "symmetric":
                new |= {(o, p, s) for s, q, o in edges if q == p}
            elif kind == "inverse":
                new |= {(o, other, s) for s, q, o in edges if q == p}
                new |= {(o, p, s) for s, q, o in edges if q == other}
            else:
                outs = {}
                for s, q, o in edges:
                    if q == p:
                        outs.setdefault(s, set()).add(o)
                for s, q, o in edges:
                    if q == p:
                        new |= {(s, p, c) for c in outs.get(o, ())}
        if not new <= edges:
            edges |= new
            changed = True
            if len(edges) > MAX_EDGES:
                raise KgError("closure exceeds 5000 edges")
    nodes = sorted({x for s, _, o in edges for x in (s, o)})
    parent = {n: n for n in nodes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for s, _, o in edges:
        a, b = find(s), find(o)
        if a != b:
            parent[max(a, b)] = min(a, b)
    outdeg = {n: 0 for n in nodes}
    indeg = {n: 0 for n in nodes}
    for s, _, o in edges:
        outdeg[s] += 1
        indeg[o] += 1
    listed = [[s, p, o, "stated" if (s, p, o) in stated else "inferred"] for s, p, o in sorted(edges)]
    return {
        "status": "completed",
        "nodes": nodes,
        "edges": listed,
        "stated_edges": len(stated),
        "inferred_edges": len(edges) - len(stated),
        "out_degree": outdeg,
        "in_degree": indeg,
        "components": len({find(n) for n in nodes}),
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
