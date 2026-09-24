"""Phylogenetics toolkit: pairwise evolutionary distances, UPGMA and
neighbor-joining tree building, tree stats.

PROVENANCE
- Jukes-Cantor distance: d = -3/4 ln(1 - 4p/3). Jukes TH, Cantor CR (1969)
  "Evolution of protein molecules", in Munro (ed.) Mammalian Protein
  Metabolism III, Academic Press, pp 21-132.
- Kimura 2-parameter distance: d = -1/2 ln(1 - 2P - Q) - 1/4 ln(1 - 2Q),
  P = transition fraction, Q = transversion fraction. Kimura M (1980)
  "A simple method for estimating evolutionary rates of base substitutions
  through comparative studies of nucleotide sequences", J Mol Evol
  16:111-120.
- UPGMA: Sokal RR, Michener CD (1958) "A statistical method for evaluating
  systematic relationships", Univ Kansas Sci Bull 38:1409-1438. Average
  linkage weighted by cluster size; merge height d/2 (ultrametric).
- Neighbor-joining: Saitou N, Nei M (1987) "The neighbor-joining method: a
  new method for reconstructing phylogenetic trees", Mol Biol Evol
  4:406-425. Q-criterion (n-2)d_ij - r_i - r_j with r_i the row sum; limb
  lengths d_iu = (d_ij + (r_i - r_j)/(n-2))/2, d_ju = d_ij - d_iu; final
  three clusters resolved as a star. NJ recovers the true tree from an
  exactly additive matrix - used as the exactness oracle in the tests.
- Cophenetic (patristic) distances: root-to-pair path through the MRCA,
  composed from bio.newick.

CONVENTIONS (documented next to every function)
- Aligned sequences only: all sequences must have equal length.
- Pairwise deletion: any column where EITHER sequence carries a gap
  ('-' or '.') or a non-ACGT base is dropped for that pair only (the
  MEGA-style pairwise-deletion default). A pair with no comparable columns
  raises ValueError.
- Saturation is reported, not clamped: JC69 is undefined for p >= 3/4 and
  K80 for 1-2P-Q <= 0 or 1-2Q <= 0; those pairs return math.inf.
- Deterministic ties: the first minimal pair in matrix order joins (both
  UPGMA and NJ).
- NJ trees are UNROOTED; the returned root dict is only the serialization
  handle bio.newick requires. NJ branch lengths may go negative on
  non-additive matrices - kept, not clamped.
"""
from __future__ import annotations

import math

from . import newick as _nw

_TS = frozenset({("A", "G"), ("G", "A"), ("C", "T"), ("T", "C")})


def _site_counts(a: str, b: str) -> dict:
    """Per-pair column counts after pairwise deletion of gap/non-ACGT
    columns."""
    a, b = a.upper(), b.upper()
    if len(a) != len(b):
        raise ValueError(f"aligned sequences must have equal length "
                         f"({len(a)} vs {len(b)})")
    total = diffs = ts = tv = 0
    for x, y in zip(a, b):
        if x not in "ACGT" or y not in "ACGT":
            continue  # pairwise deletion of gap/ambiguous columns
        total += 1
        if x != y:
            diffs += 1
            if (x, y) in _TS:
                ts += 1
            else:
                tv += 1
    if total == 0:
        raise ValueError("no comparable columns after pairwise deletion")
    return {"sites": total, "diffs": diffs, "transitions": ts,
            "transversions": tv}


def p_distance(a: str, b: str) -> float:
    """Fraction of differing comparable sites."""
    c = _site_counts(a, b)
    return c["diffs"] / c["sites"]


def jc69_distance(a: str, b: str) -> float:
    """Jukes-Cantor 1969 distance; math.inf when p >= 3/4 (saturation)."""
    p = p_distance(a, b)
    if p >= 0.75:
        return math.inf
    return -0.75 * math.log(1.0 - 4.0 * p / 3.0)


def k80_distance(a: str, b: str) -> float:
    """Kimura 2-parameter 1980 distance; math.inf outside the log domain."""
    c = _site_counts(a, b)
    p, q = c["transitions"] / c["sites"], c["transversions"] / c["sites"]
    x, y = 1.0 - 2.0 * p - q, 1.0 - 2.0 * q
    if x <= 0.0 or y <= 0.0:
        return math.inf
    return -0.5 * math.log(x) - 0.25 * math.log(y)


_MODELS = {"pdistance": p_distance, "jc69": jc69_distance, "k80": k80_distance}


def distance_matrix(seqs: dict, model: str = "pdistance") -> dict:
    """Symmetric pairwise distance matrix over an alignment dict
    (name -> sequence). Names keep insertion order."""
    if model not in _MODELS:
        raise ValueError(f"model must be one of {sorted(_MODELS)}, "
                         f"got {model!r}")
    names = list(seqs)
    fn = _MODELS[model]
    n = len(names)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = fn(seqs[names[i]], seqs[names[j]])
            matrix[i][j] = matrix[j][i] = d
    return {"names": names, "model": model, "matrix": matrix}


def _pairs(d: dict):
    return ((dist, i, j) for (i, j), dist in d.items())


def upgma(names: list, matrix: list) -> dict:
    """UPGMA tree (Sokal & Michener 1958) from a square distance matrix.
    Rooted and ultrametric; merge height = d/2, size-weighted average
    linkage. Deterministic: first minimal pair in matrix order joins."""
    n = len(names)
    if n < 2:
        raise ValueError("need at least 2 taxa")
    d = {(i, j): matrix[i][j] for i in range(n) for j in range(i + 1, n)}
    height = {i: 0.0 for i in range(n)}
    size = {i: 1 for i in range(n)}
    node = {i: {"name": names[i], "length": None, "children": []}
            for i in range(n)}
    active = list(range(n))
    nxt = n
    while len(active) > 1:
        dist, i, j = min(_pairs({k: v for k, v in d.items()
                                 if k[0] in active and k[1] in active}))
        h = dist / 2.0
        node[i]["length"] = h - height[i]
        node[j]["length"] = h - height[j]
        u = nxt; nxt += 1
        node[u] = {"name": None, "length": None,
                   "children": [node[i], node[j]]}
        height[u] = h
        size[u] = size[i] + size[j]
        for k in active:
            if k in (i, j):
                continue
            dik = d.pop((min(i, k), max(i, k)))
            djk = d.pop((min(j, k), max(j, k)))
            d[(min(u, k), max(u, k))] = \
                (dik * size[i] + djk * size[j]) / size[u]
        d.pop((min(i, j), max(i, j)), None)
        active = [k for k in active if k not in (i, j)] + [u]
    return node[active[0]]


def neighbor_joining(names: list, matrix: list) -> dict:
    """Neighbor-joining tree (Saitou & Nei 1987). Unrooted - the returned
    root dict is only the Newick serialization handle. Exact on additive
    matrices; negative branch lengths kept, not clamped."""
    n = len(names)
    if n < 2:
        raise ValueError("need at least 2 taxa")
    if n == 2:
        return {"name": None, "length": None, "children": [
            {"name": names[0], "length": matrix[0][1] / 2.0, "children": []},
            {"name": names[1], "length": matrix[0][1] / 2.0, "children": []}]}
    d = {(i, j): matrix[i][j] for i in range(n) for j in range(i + 1, n)}
    node = {i: {"name": names[i], "length": None, "children": []}
            for i in range(n)}
    active = list(range(n))
    nxt = n

    def dist(i, j):
        return d[(min(i, j), max(i, j))]

    while len(active) > 3:
        m = len(active)
        r = {i: sum(dist(i, k) for k in active if k != i) for i in active}
        q, i, j = min(((m - 2) * dist(i, j) - r[i] - r[j], i, j)
                      for x, i in enumerate(active) for j in active[x + 1:])
        dij = dist(i, j)
        diu = (dij + (r[i] - r[j]) / (m - 2)) / 2.0
        node[i]["length"] = diu
        node[j]["length"] = dij - diu
        u = nxt; nxt += 1
        node[u] = {"name": None, "length": None,
                   "children": [node[i], node[j]]}
        for k in active:
            if k in (i, j):
                continue
            d[(min(u, k), max(u, k))] = \
                (dist(i, k) + dist(j, k) - dij) / 2.0
        for k in active:
            if k not in (i, j):
                d.pop((min(i, k), max(i, k)), None)
                d.pop((min(j, k), max(j, k)), None)
        d.pop((min(i, j), max(i, j)), None)
        active = [k for k in active if k not in (i, j)] + [u]
    x, y, z = active
    node[x]["length"] = (dist(x, y) + dist(x, z) - dist(y, z)) / 2.0
    node[y]["length"] = (dist(x, y) + dist(y, z) - dist(x, z)) / 2.0
    node[z]["length"] = (dist(x, z) + dist(y, z) - dist(x, y)) / 2.0
    return {"name": None, "length": None,
            "children": [node[x], node[y], node[z]]}


def build_tree(names: list, matrix: list, method: str = "nj") -> dict:
    """Build a tree from a distance matrix: method 'upgma' or 'nj'."""
    if method == "upgma":
        return upgma(names, matrix)
    if method == "nj":
        return neighbor_joining(names, matrix)
    raise ValueError(f"method must be 'upgma' or 'nj', got {method!r}")


def total_branch_length(root: dict) -> float:
    """Sum of all branch lengths (None lengths count as 0)."""
    return sum(n["length"] or 0.0 for n in _nw.preorder(root))


def cophenetic(root: dict) -> dict:
    """Cophenetic (patristic) distance matrix between all leaf pairs,
    composed from bio.newick's MRCA-path distance."""
    names = _nw.leaves(root)
    n = len(names)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j] = matrix[j][i] = _nw.distance(root, names[i],
                                                       names[j])
    return {"names": names, "matrix": matrix}
