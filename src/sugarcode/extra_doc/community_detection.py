"""Community Detection - exact greedy modularity communities over a caller-supplied graph.

Pure function over caller data. No retrieval, no network, no clock, no floats.
Input: n (integer 3..20, nodes are 0..n-1) and edges (1..60 [a, b] pairs of distinct
nodes forming a simple undirected graph: no self-loop, no repeated edge in either order).
Every node starts in its own community. Repeatedly the two communities joined by at
least one edge whose merge raises the modularity the most are merged, using the exact
gain l_AB / m - D_A * D_B / (2 m^2) (l_AB edges between them, D the degree sum of each,
m the edge count). Ties go to the pair whose smallest members are lexicographically
smallest as (smaller community first). The process stops when no merge has a positive
gain. The result lists the final communities (each sorted, ordered by smallest member),
the merge steps with their exact gains, the modularity Q of the result as an exact
Fraction and the connected components. Modularity is
Q = sum over communities of (internal edges / m - (degree sum / (2 m))^2).

Scope: PARTIAL for the Community Detection line. It runs one deterministic greedy
agglomerative method (the Clauset-Newman-Moore rule) on an unweighted undirected graph.
It does no Louvain or Leiden refinement, no label propagation, no overlapping or
hierarchical output beyond the merge steps, no weights or directions, and no check that
the partition is the modularity optimum.

Not claimed: that the communities are real groups, that the greedy result is optimal, that
modularity measures community quality in general, that the graph is real, or anything about
the real world. Every claim flag in the result is False.
"""
from fractions import Fraction

MIN_N = 3
MAX_N = 20
MIN_EDGES = 1
MAX_EDGES = 60
_TOP = frozenset({"n", "edges"})

NOT_CLAIMED = (
    "the communities are real groups",
    "the greedy partition is optimal",
    "modularity measures community quality",
    "the graph is real",
    "real-world outcome",
)
CLAIMS = {"communities_real": False, "optimal": False, "quality": False, "graph_real": False, "real_world": False}


class CommunityError(ValueError):
    pass


def _int(v, name):
    if isinstance(v, bool) or not isinstance(v, int):
        raise CommunityError(f"{name} must be an int")
    return v


def community_detection(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise CommunityError("data keys must be exactly n, edges")
    n = _int(data["n"], "n")
    if not MIN_N <= n <= MAX_N:
        raise CommunityError("n out of range")
    edges_in = data["edges"]
    if not isinstance(edges_in, list):
        raise CommunityError("edges must be a list")
    if not MIN_EDGES <= len(edges_in) <= MAX_EDGES:
        raise CommunityError("edges length out of range")
    seen = set()
    for e in edges_in:
        if not isinstance(e, list) or len(e) != 2:
            raise CommunityError("edge must be an [a, b] list")
        a, b = _int(e[0], "node"), _int(e[1], "node")
        if not (0 <= a < n and 0 <= b < n):
            raise CommunityError("node out of range")
        if a == b:
            raise CommunityError("self-loops are not allowed")
        key = (min(a, b), max(a, b))
        if key in seen:
            raise CommunityError("duplicate edge")
        seen.add(key)
    m = len(seen)
    deg = [0] * n
    for a, b in seen:
        deg[a] += 1
        deg[b] += 1
    groups = {i: [i] for i in range(n)}
    steps = []
    while True:
        best = None
        ids = sorted(groups, key=lambda g: groups[g][0])
        for i, ga in enumerate(ids):
            for gb in ids[i + 1:]:
                sa, sb = set(groups[ga]), set(groups[gb])
                between = sum(1 for a, b in seen if (a in sa and b in sb) or (a in sb and b in sa))
                if between == 0:
                    continue
                gain = Fraction(between, m) - Fraction(sum(deg[x] for x in sa) * sum(deg[x] for x in sb), 2 * m * m)
                if best is None or gain > best[0]:
                    best = (gain, ga, gb)
        if best is None or best[0] <= 0:
            break
        gain, ga, gb = best
        steps.append({"merged": [list(groups[ga]), list(groups[gb])], "gain": str(gain)})
        groups[ga] = sorted(groups[ga] + groups[gb])
        del groups[gb]
    comms = sorted(groups.values(), key=lambda c: c[0])
    q = Fraction(0)
    for c in comms:
        sc = set(c)
        inside = sum(1 for a, b in seen if a in sc and b in sc)
        q += Fraction(inside, m) - Fraction(sum(deg[x] for x in c), 2 * m) ** 2
    comp_of = list(range(n))
    for a, b in sorted(seen):
        ca, cb = comp_of[a], comp_of[b]
        if ca != cb:
            comp_of = [ca if x == cb else x for x in comp_of]
    components = sorted(sorted(i for i in range(n) if comp_of[i] == c) for c in set(comp_of))
    return {
        "n": n,
        "edge_count": m,
        "communities": comms,
        "merge_steps": steps,
        "modularity": str(q),
        "components": components,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
