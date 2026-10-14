import copy
import itertools
from fractions import Fraction

import pytest

from sugarcode.extra_doc import community_detection as m
from sugarcode.extra_doc.community_detection import CommunityError, community_detection as run

KEYS = "data keys must be exactly n, edges"
LITERAL_NOT_CLAIMED = [
    "the communities are real groups",
    "the greedy partition is optimal",
    "modularity measures community quality",
    "the graph is real",
    "real-world outcome",
]
TWO_TRI = [[0, 1], [1, 2], [0, 2], [3, 4], [4, 5], [3, 5], [2, 3]]


def d(n, edges):
    return {"n": n, "edges": [list(e) for e in edges]}


def bad(data, msg):
    with pytest.raises(CommunityError) as e:
        run(data)
    assert str(e.value) == msg


def q_matrix(n, edges, comm):
    # Q = 1/(2m) * sum_ij (A_ij - k_i k_j / 2m) [c_i == c_j], from the adjacency matrix
    A = [[0] * n for _ in range(n)]
    for a, b in edges:
        A[a][b] = A[b][a] = 1
    k = [sum(r) for r in A]
    m2 = sum(k)
    return sum(Fraction(A[i][j]) - Fraction(k[i] * k[j], m2) for i in range(n) for j in range(n) if comm[i] == comm[j]) / m2


def oracle(n, edges):
    # greedy by explicit partition modularity: try every adjacent pair, keep the best resulting Q;
    # ties keep the pair whose smaller community (by smallest member) comes first, then the other
    adj = {tuple(sorted(e)) for e in edges}
    parts = [[i] for i in range(n)]
    while True:
        cur = q_matrix(n, edges, comm_of(parts, n))
        best = None
        order = sorted(parts, key=lambda c: c[0])
        for i, a in enumerate(order):
            for b in order[i + 1:]:
                if not any(tuple(sorted((x, y))) in adj for x in a for y in b):
                    continue
                new = [c for c in parts if c is not a and c is not b] + [sorted(a + b)]
                gain = q_matrix(n, edges, comm_of(new, n)) - cur
                if best is None or gain > best[0]:
                    best = (gain, new)
        if best is None or best[0] <= 0:
            return sorted(parts, key=lambda c: c[0]), cur
        parts = best[1]


def comm_of(parts, n):
    out = [0] * n
    for idx, c in enumerate(parts):
        for x in c:
            out[x] = idx
    return out


def test_two_triangles_hand_case():
    out = run(d(6, TWO_TRI))
    assert out["communities"] == [[0, 1, 2], [3, 4, 5]]
    assert out["modularity"] == "5/14" and out["edge_count"] == 7
    assert out["components"] == [[0, 1, 2, 3, 4, 5]]
    first = out["merge_steps"][0]
    assert first == {"merged": [[0], [1]], "gain": "5/49"}
    assert len(out["merge_steps"]) == 4


def test_matches_explicit_modularity_oracle():
    graphs = [
        (6, TWO_TRI),
        (7, [[0, 1], [0, 2], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [4, 6]]),
        (6, [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0]]),
        (5, [[0, 1], [0, 2], [0, 3], [0, 4]]),
        (7, [[0, 1], [1, 2], [0, 2], [3, 4], [4, 5]]),
        (8, [[0, 1], [2, 3], [4, 5], [6, 7], [1, 2], [3, 4], [5, 6]]),
    ]
    for n, edges in graphs:
        out = run(d(n, edges))
        comms, q = oracle(n, edges)
        assert out["communities"] == comms, edges
        assert out["modularity"] == str(q), edges
        assert q == q_matrix(n, edges, comm_of(out["communities"], n))


def test_merge_gains_replay_to_final_modularity():
    out = run(d(6, TWO_TRI))
    total = Fraction(0)
    for s in out["merge_steps"]:
        total += Fraction(s["gain"])
        assert Fraction(s["gain"]) > 0
    start = -sum(Fraction(dg, 14) ** 2 for dg in (2, 2, 3, 3, 2, 2))
    assert start + total == Fraction(out["modularity"])


def test_components_and_isolated_nodes():
    out = run(d(6, [[0, 1], [1, 2], [3, 4]]))
    assert out["components"] == [[0, 1, 2], [3, 4], [5]]
    assert [5] in out["communities"]
    out = run(d(4, [[0, 1], [2, 3]]))
    assert out["communities"] == [[0, 1], [2, 3]] and out["modularity"] == "1/2"


def test_tie_break_prefers_smallest_pair():
    # path 0-1-2: merging (0,1) and (1,2) have the same gain; (0,1) must win, then 2 joins it or not
    out = run(d(3, [[0, 1], [1, 2]]))
    assert out["merge_steps"][0]["merged"] == [[0], [1]]
    # same graph with labels reversed in the edge list must give the same result
    assert run(d(3, [[2, 1], [1, 0]])) == out


def test_input_order_does_not_change_result():
    a = run(d(6, TWO_TRI))
    b = run(d(6, list(reversed([[y, x] for x, y in TWO_TRI]))))
    assert a == b


def test_claims_and_input_not_mutated():
    data = d(4, [[0, 1], [1, 2]])
    before = copy.deepcopy(data)
    out = run(data)
    assert data == before
    assert out["claims"] == {"communities_real": False, "optimal": False, "quality": False, "graph_real": False, "real_world": False}
    out["claims"]["real_world"] = True
    out["not_claimed"].append("x")
    out["communities"][0].append(99)
    again = run(data)
    assert again["claims"]["real_world"] is False and again["not_claimed"] == LITERAL_NOT_CLAIMED
    assert 99 not in again["communities"][0]
    assert tuple(again["not_claimed"]) == m.NOT_CLAIMED


def test_constants():
    assert (m.MIN_N, m.MAX_N, m.MIN_EDGES, m.MAX_EDGES) == (3, 20, 1, 60)


def test_refusals_and_caps():
    for x in (None, [], {"n": 3}, dict(d(3, [[0, 1]]), extra=1)):
        bad(x, KEYS)
    for v in (True, 3.0, "3", None):
        bad(d(3, [[0, 1]]) | {"n": v}, "n must be an int")
    bad(d(2, [[0, 1]]), "n out of range")
    bad(d(21, [[0, 1]]), "n out of range")
    run(d(20, [[0, 1]]))
    bad(d(3, [[0, 1]]) | {"edges": "ab"}, "edges must be a list")
    bad(d(3, []), "edges length out of range")
    pairs = list(itertools.combinations(range(12), 2))
    run(d(12, pairs[:60]))
    bad(d(12, pairs[:61]), "edges length out of range")
    for e in ([0], [0, 1, 2], (0, 1), "ab"):
        bad(d(3, [[0, 1]]) | {"edges": [e]}, "edge must be an [a, b] list")
    for v in (True, 1.0, "1"):
        bad(d(3, [[0, 1]]) | {"edges": [[v, 1]]}, "node must be an int")
        bad(d(3, [[0, 1]]) | {"edges": [[0, v]]}, "node must be an int")
    for e in ([0, 3], [3, 0], [1, 3], [3, 2], [-1, 1], [1, -1]):
        bad(d(3, [e]), "node out of range")
    run(d(3, [[2, 1]]))
    bad(d(3, [[1, 1]]), "self-loops are not allowed")
    bad(d(3, [[0, 1], [0, 1]]), "duplicate edge")
    bad(d(3, [[0, 1], [1, 0]]), "duplicate edge")


PINNED = [
    # (n, edges, communities, modularity, components, gains)
    (4, [[3, 1], [0, 2], [0, 3], [2, 1], [2, 3]], [[0, 1, 2, 3]], "0", [[0, 1, 2, 3]], ["2/25", "1/10", "2/25"]),
    (5, [[4, 1], [0, 2], [1, 0], [2, 1], [4, 3], [3, 2], [0, 4]], [[0, 1, 4], [2, 3]], "3/98", [[0, 1, 2, 3, 4]],
     ["4/49", "5/98", "5/49"]),
    (4, [[3, 0], [3, 1], [2, 3], [0, 1]], [[0, 1], [2, 3]], "0", [[0, 1, 2, 3]], ["5/32", "1/8"]),
    (6, [[2, 4], [5, 4], [3, 5], [4, 3], [5, 0]], [[0, 3, 5], [1], [2, 4]], "2/25", [[0, 2, 3, 4, 5], [1]],
     ["7/50", "7/50", "1/25"]),
]


def test_pinned_cases_found_by_search_agree_with_oracle():
    for n, edges, comms, q, comps, gains in PINNED:
        out = run(d(n, edges))
        assert out["communities"] == comms and out["modularity"] == q and out["components"] == comps
        assert [s["gain"] for s in out["merge_steps"]] == gains
        ref_comms, ref_q = oracle(n, edges)
        assert ref_comms == comms and str(ref_q) == q


def test_zero_gain_merge_is_not_taken_and_unsorted_merge_lists_are_sorted():
    # last pinned case: a zero-gain merge exists at the end of the second graph and must not happen
    out = run(d(4, [[3, 0], [3, 1], [2, 3], [0, 1]]))
    assert out["communities"] == [[0, 1], [2, 3]]
    # merging {0,2} with {1,3}-style groups keeps members sorted inside each community
    out = run(d(4, [[3, 1], [0, 2], [0, 3], [2, 1], [2, 3]]))
    for c in out["communities"]:
        assert c == sorted(c)
    for s in out["merge_steps"]:
        assert all(part == sorted(part) for part in s["merged"])
