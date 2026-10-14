"""Network Motif Analysis - exact small-subgraph counts over a caller-supplied graph.

Pure function over caller data. No retrieval, no network, no clock, no floats.
Input: n (integer 4..12, nodes are 0..n-1) and edges (0..40 [a, b] pairs of distinct
nodes forming a simple undirected graph: no self-loop, no repeated edge in either
order). The result counts, over all node subsets, the induced subgraphs:
  triads: the 3-node subsets with 0, 1, 2 and 3 edges;
  tetrads: the 4-node subsets by their induced shape: empty, one edge, two adjacent
    edges (path of 3 plus an isolated node), two disjoint edges, triangle plus isolated
    node, star, path of 4, 4-cycle, paw (triangle with a pendant), diamond and K4;
and reports the triangle count, the number of wedges (paths of 2 edges, counted by
centre), the global clustering coefficient 3 * triangles / wedges (None when there are
no wedges) and the exact expected triangle count in a random graph with the same number
of nodes and edges drawn uniformly (C(M-3, m-3) / C(M, m) * C(n, 3) with M = C(n, 2)),
with the observed-to-expected ratio (None when the expected count is 0).

Scope: PARTIAL for the Network Motif Analysis line. It counts undirected induced
motifs of 3 and 4 nodes and compares triangles with one exact null expectation. It does no
directed or larger motifs, no sampled or degree-preserving null models, no z-scores or
p-values, and no claim that any count is a significant motif.

Not claimed: that a motif is statistically significant or functionally meaningful, that
the graph is real, or anything about the real world. Every claim flag in the result is
False.
"""
from fractions import Fraction
from itertools import combinations
from math import comb

MIN_N = 4
MAX_N = 12
MAX_EDGES = 40
_TOP = frozenset({"n", "edges"})

# sorted induced degree tuple -> shape name (unique per 4-node shape)
_SHAPES = {
    (0, 0, 0, 0): "empty",
    (0, 0, 1, 1): "one_edge",
    (0, 1, 1, 2): "two_adjacent_edges",
    (1, 1, 1, 1): "two_disjoint_edges",
    (0, 2, 2, 2): "triangle_plus_isolated",
    (1, 1, 1, 3): "star",
    (1, 1, 2, 2): "path_4",
    (2, 2, 2, 2): "cycle_4",
    (1, 2, 2, 3): "paw",
    (2, 2, 3, 3): "diamond",
    (3, 3, 3, 3): "k4",
}
SHAPE_NAMES = tuple(_SHAPES[k] for k in sorted(_SHAPES))

NOT_CLAIMED = (
    "any motif is statistically significant",
    "any motif is functionally meaningful",
    "the graph is real",
    "real-world outcome",
)
CLAIMS = {"significant": False, "meaningful": False, "graph_real": False, "real_world": False}


class MotifError(ValueError):
    pass


def _int(v, name):
    if isinstance(v, bool) or not isinstance(v, int):
        raise MotifError(f"{name} must be an int")
    return v


def network_motifs(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise MotifError("data keys must be exactly n, edges")
    n = _int(data["n"], "n")
    if not MIN_N <= n <= MAX_N:
        raise MotifError("n out of range")
    edges_in = data["edges"]
    if not isinstance(edges_in, list):
        raise MotifError("edges must be a list")
    if len(edges_in) > MAX_EDGES:
        raise MotifError("edges length out of range")
    seen = set()
    for e in edges_in:
        if not isinstance(e, list) or len(e) != 2:
            raise MotifError("edge must be an [a, b] list")
        a, b = _int(e[0], "node"), _int(e[1], "node")
        if not (0 <= a < n and 0 <= b < n):
            raise MotifError("node out of range")
        if a == b:
            raise MotifError("self-loops are not allowed")
        key = (min(a, b), max(a, b))
        if key in seen:
            raise MotifError("duplicate edge")
        seen.add(key)
    has = lambda a, b: (a, b) in seen if a < b else (b, a) in seen
    triads = [0, 0, 0, 0]
    for a, b, c in combinations(range(n), 3):
        triads[has(a, b) + has(a, c) + has(b, c)] += 1
    shapes = {name: 0 for name in SHAPE_NAMES}
    for quad in combinations(range(n), 4):
        deg = sorted(sum(1 for y in quad if y != x and has(x, y)) for x in quad)
        shapes[_SHAPES[tuple(deg)]] += 1
    triangles = triads[3]
    wedges = sum(comb(sum(1 for y in range(n) if y != x and has(x, y)), 2) for x in range(n))
    m = len(seen)
    pairs = comb(n, 2)
    expected = Fraction(comb(pairs - 3, m - 3), comb(pairs, m)) * comb(n, 3) if m >= 3 else Fraction(0)
    return {
        "n": n,
        "edge_count": m,
        "triads": {"0_edges": triads[0], "1_edge": triads[1], "2_edges": triads[2], "3_edges": triads[3]},
        "tetrads": shapes,
        "triangles": triangles,
        "wedges": wedges,
        "global_clustering": None if wedges == 0 else str(Fraction(3 * triangles, wedges)),
        "expected_triangles": str(expected),
        "triangle_ratio": None if expected == 0 else str(Fraction(triangles) / expected),
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
