import copy
import itertools
from fractions import Fraction

import pytest

from sugarcode.extra_doc import network_motifs as m
from sugarcode.extra_doc.network_motifs import MotifError, network_motifs as run

KEYS = "data keys must be exactly n, edges"
LITERAL_NOT_CLAIMED = [
    "any motif is statistically significant",
    "any motif is functionally meaningful",
    "the graph is real",
    "real-world outcome",
]
SHAPE_NAMES = [
    "cycle_4", "diamond", "empty", "k4", "one_edge", "paw", "path_4", "star",
    "triangle_plus_isolated", "two_adjacent_edges", "two_disjoint_edges",
]
# reference edge lists on nodes 0..3, one per shape, independent of the degree-tuple table
REFERENCE = {
    "empty": [],
    "one_edge": [(0, 1)],
    "two_adjacent_edges": [(0, 1), (1, 2)],
    "two_disjoint_edges": [(0, 1), (2, 3)],
    "triangle_plus_isolated": [(0, 1), (1, 2), (0, 2)],
    "star": [(0, 1), (0, 2), (0, 3)],
    "path_4": [(0, 1), (1, 2), (2, 3)],
    "cycle_4": [(0, 1), (1, 2), (2, 3), (3, 0)],
    "paw": [(0, 1), (1, 2), (0, 2), (2, 3)],
    "diamond": [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)],
    "k4": [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)],
}


def d(n, edges):
    return {"n": n, "edges": [list(e) for e in edges]}


def bad(data, msg):
    with pytest.raises(MotifError) as e:
        run(data)
    assert str(e.value) == msg


def canon(edges):
    return frozenset(frozenset(e) for e in edges)


def shape_of(sub_edges):
    # isomorphism test by trying every relabelling against each reference shape
    mine = canon(sub_edges)
    for name, ref in REFERENCE.items():
        if len(ref) != len(mine):
            continue
        for perm in itertools.permutations(range(4)):
            if canon([(perm[a], perm[b]) for a, b in ref]) == mine:
                return name
    raise AssertionError(sub_edges)


def oracle(n, edges):
    es = canon(edges)
    triads = [0] * 4
    for tri in itertools.combinations(range(n), 3):
        triads[sum(1 for p in itertools.combinations(tri, 2) if frozenset(p) in es)] += 1
    shapes = {k: 0 for k in REFERENCE}
    for quad in itertools.combinations(range(n), 4):
        idx = {v: i for i, v in enumerate(quad)}
        sub = [(idx[a], idx[b]) for a, b in itertools.combinations(quad, 2) if frozenset((a, b)) in es]
        shapes[shape_of(sub)] += 1
    return triads, shapes


def expected_triangles_by_enumeration(n, m_edges):
    allp = list(itertools.combinations(range(n), 2))
    total = Fraction(0)
    count = 0
    for chosen in itertools.combinations(allp, m_edges):
        s = set(chosen)
        total += sum(1 for t in itertools.combinations(range(n), 3)
                     if all(p in s for p in itertools.combinations(t, 2)))
        count += 1
    return total / count


def test_hand_case_triangle_with_tail():
    out = run(d(5, [[0, 1], [1, 2], [0, 2], [2, 3]]))
    assert out["triads"] == {"0_edges": 2, "1_edge": 5, "2_edges": 2, "3_edges": 1}
    assert out["tetrads"]["paw"] == 1 and out["tetrads"]["triangle_plus_isolated"] == 1
    assert out["tetrads"]["two_adjacent_edges"] == 2 and out["tetrads"]["one_edge"] == 1
    assert sum(out["tetrads"].values()) == 5
    assert out["triangles"] == 1 and out["wedges"] == 5 and out["global_clustering"] == "3/5"
    assert out["expected_triangles"] == "1/3" and out["triangle_ratio"] == "3"
    assert out["edge_count"] == 4 and out["n"] == 5


def test_shape_names_pinned_and_each_shape_detected():
    assert sorted(m.SHAPE_NAMES) == sorted(SHAPE_NAMES) and len(m.SHAPE_NAMES) == 11
    for name, ref in REFERENCE.items():
        out = run(d(4, ref))
        assert out["tetrads"][name] == 1 and sum(out["tetrads"].values()) == 1, name
        assert out["tetrads"] == {k: (1 if k == name else 0) for k in REFERENCE}


def test_relabelled_shapes_are_still_detected():
    for name, ref in REFERENCE.items():
        for perm in ((3, 2, 1, 0), (1, 3, 0, 2), (2, 0, 3, 1)):
            out = run(d(4, [(perm[a], perm[b]) for a, b in ref]))
            assert out["tetrads"][name] == 1, (name, perm)


def test_census_matches_isomorphism_oracle():
    graphs = [
        (6, [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0], [0, 3]]),
        (7, [[0, 1], [0, 2], [0, 3], [4, 5], [5, 6], [4, 6], [3, 4]]),
        (6, [[0, 1], [2, 3], [4, 5]]),
        (6, list(itertools.combinations(range(6), 2))),
        (8, [[0, 1], [1, 2], [2, 0], [2, 3], [3, 4], [4, 5], [5, 3], [6, 7], [1, 6]]),
        (5, []),
    ]
    for n, edges in graphs:
        out = run(d(n, edges))
        triads, shapes = oracle(n, edges)
        assert [out["triads"][k] for k in ("0_edges", "1_edge", "2_edges", "3_edges")] == triads, edges
        assert out["tetrads"] == shapes, edges
        assert sum(shapes.values()) == len(list(itertools.combinations(range(n), 4)))


def test_expected_triangles_match_full_enumeration():
    for n, mm in ((4, 3), (5, 4), (5, 7), (6, 5), (6, 10)):
        edges = list(itertools.combinations(range(n), 2))[:mm]
        assert run(d(n, edges))["expected_triangles"] == str(expected_triangles_by_enumeration(n, mm)), (n, mm)


def test_expected_zero_below_three_edges_and_none_fields():
    for k in (0, 1, 2):
        out = run(d(5, [[0, 1], [1, 2]][:k]))
        assert out["expected_triangles"] == "0" and out["triangle_ratio"] is None
    out = run(d(4, []))
    assert out["wedges"] == 0 and out["global_clustering"] is None
    out = run(d(4, [[0, 1], [2, 3]]))
    assert out["wedges"] == 0 and out["global_clustering"] is None
    out = run(d(4, [[0, 1], [1, 2], [2, 3]]))
    assert out["triangles"] == 0 and out["global_clustering"] == "0" and out["triangle_ratio"] == "0"


def test_complete_graph_values():
    out = run(d(5, list(itertools.combinations(range(5), 2))))
    assert out["triangles"] == 10 and out["wedges"] == 30 and out["global_clustering"] == "1"
    assert out["expected_triangles"] == "10" and out["triangle_ratio"] == "1"
    assert out["tetrads"]["k4"] == 5


def test_edge_order_and_direction_do_not_matter():
    a = run(d(5, [[0, 1], [1, 2], [0, 2], [2, 3]]))
    b = run(d(5, [[3, 2], [2, 0], [2, 1], [1, 0]]))
    assert a == b


def test_claims_and_input_not_mutated():
    data = d(4, [[0, 1], [1, 2]])
    before = copy.deepcopy(data)
    out = run(data)
    assert data == before
    assert out["claims"] == {"significant": False, "meaningful": False, "graph_real": False, "real_world": False}
    out["claims"]["real_world"] = True
    out["not_claimed"].append("x")
    out["tetrads"]["k4"] = 9
    again = run(data)
    assert again["claims"]["real_world"] is False and again["not_claimed"] == LITERAL_NOT_CLAIMED
    assert again["tetrads"]["k4"] == 0
    assert tuple(again["not_claimed"]) == m.NOT_CLAIMED


def test_constants():
    assert (m.MIN_N, m.MAX_N, m.MAX_EDGES) == (4, 12, 40)


def test_refusals_and_caps():
    for x in (None, [], {"n": 4}, dict(d(4, []), extra=1)):
        bad(x, KEYS)
    for v in (True, 4.0, "4", None):
        bad(d(4, []) | {"n": v}, "n must be an int")
    bad(d(3, []), "n out of range")
    bad(d(13, []), "n out of range")
    run(d(4, []))
    run(d(12, []))
    bad(d(4, []) | {"edges": "ab"}, "edges must be a list")
    pairs = list(itertools.combinations(range(12), 2))
    run(d(12, pairs[:40]))
    bad(d(12, pairs[:41]), "edges length out of range")
    for e in ([0], [0, 1, 2], (0, 1), "ab"):
        bad(d(4, []) | {"edges": [e]}, "edge must be an [a, b] list")
    for v in (True, 1.0, "1"):
        bad(d(4, []) | {"edges": [[v, 1]]}, "node must be an int")
        bad(d(4, []) | {"edges": [[0, v]]}, "node must be an int")
    for e in ([0, 4], [4, 0], [1, 4], [4, 2], [-1, 1], [1, -1]):
        bad(d(4, [e]), "node out of range")
    run(d(4, [[3, 2]]))
    bad(d(4, [[1, 1]]), "self-loops are not allowed")
    bad(d(4, [[0, 1], [0, 1]]), "duplicate edge")
    bad(d(4, [[0, 1], [1, 0]]), "duplicate edge")
