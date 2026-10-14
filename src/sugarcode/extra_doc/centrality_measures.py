"""Centrality Measures - exact node importance scores over a caller-supplied graph.

Pure function over caller data. No retrieval, no network, no clock, no floats.
Input: n (integer 3..20, nodes are 0..n-1) and edges (0..60 [a, b] pairs of distinct
nodes forming a simple undirected graph: no self-loop, and no repeated edge in either
order). For every node the result gives, as exact Fractions in strings or integers:
  degree and degree centrality degree / (n - 1);
  closeness in the Wasserman-Faust form (r / (n - 1)) * (r / total distance), where r is
    the number of other nodes it reaches (0 when it reaches none);
  harmonic centrality, the sum of 1 / distance over the other nodes it reaches;
  betweenness, the sum over unordered pairs {s, t} not containing the node of the share of
    shortest s-t paths that pass through it (disconnected pairs add 0), and the same
    divided by (n - 1)(n - 2) / 2.

Scope: PARTIAL for the Centrality Measures line. It covers degree, closeness, harmonic and
betweenness on unweighted undirected graphs. It computes no eigenvector, Katz or PageRank
score (those are not exact rationals), uses no edge weights or directions, and ranks
nothing as important in the real world.

Not claimed: that a high score means a node matters, that the graph is real, that the
graph is complete, or anything about the real world. Every claim flag in the result is
False.
"""
from fractions import Fraction

MIN_N = 3
MAX_N = 20
MAX_EDGES = 60
_TOP = frozenset({"n", "edges"})

NOT_CLAIMED = (
    "a high score means a node matters",
    "the graph is real",
    "the graph is complete",
    "real-world outcome",
)
CLAIMS = {"importance": False, "graph_real": False, "graph_complete": False, "real_world": False}


class CentralityError(ValueError):
    pass


def _int(v, name):
    if isinstance(v, bool) or not isinstance(v, int):
        raise CentralityError(f"{name} must be an int")
    return v


def _bfs(adj, s):
    dist = {s: 0}
    paths = {s: 1}
    queue = [s]
    for u in queue:
        for v in adj[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                paths[v] = 0
                queue.append(v)
            if dist[v] == dist[u] + 1:
                paths[v] += paths[u]
    return dist, paths


def centrality_measures(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise CentralityError("data keys must be exactly n, edges")
    n = _int(data["n"], "n")
    if not MIN_N <= n <= MAX_N:
        raise CentralityError("n out of range")
    edges_in = data["edges"]
    if not isinstance(edges_in, list):
        raise CentralityError("edges must be a list")
    if len(edges_in) > MAX_EDGES:
        raise CentralityError("edges length out of range")
    seen = set()
    adj = {i: [] for i in range(n)}
    for e in edges_in:
        if not isinstance(e, list) or len(e) != 2:
            raise CentralityError("edge must be an [a, b] list")
        a, b = _int(e[0], "node"), _int(e[1], "node")
        if not (0 <= a < n and 0 <= b < n):
            raise CentralityError("node out of range")
        if a == b:
            raise CentralityError("self-loops are not allowed")
        key = (min(a, b), max(a, b))
        if key in seen:
            raise CentralityError("duplicate edge")
        seen.add(key)
        adj[a].append(b)
        adj[b].append(a)
    info = [_bfs(adj, s) for s in range(n)]
    pairs = Fraction((n - 1) * (n - 2), 2)
    nodes = []
    for v in range(n):
        dist = info[v][0]
        others = [d for u, d in dist.items() if u != v]
        r = len(others)
        total = sum(others)
        between = Fraction(0)
        for s in range(n):
            for t in range(s + 1, n):
                if v in (s, t) or t not in info[s][0]:
                    continue
                if v in info[s][0] and t in info[v][0] and info[s][0][v] + info[v][0][t] == info[s][0][t]:
                    between += Fraction(info[s][1][v] * info[v][1][t], info[s][1][t])
        nodes.append({
            "node": v,
            "degree": len(adj[v]),
            "degree_centrality": str(Fraction(len(adj[v]), n - 1)),
            "closeness": "0" if r == 0 else str(Fraction(r, n - 1) * Fraction(r, total)),
            "harmonic": str(sum(Fraction(1, d) for d in others)),
            "betweenness": str(between),
            "betweenness_normalized": str(between / pairs),
        })
    return {
        "n": n,
        "edge_count": len(seen),
        "nodes": nodes,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
