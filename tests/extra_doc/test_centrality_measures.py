import copy
import itertools
from fractions import Fraction

import pytest

from sugarcode.extra_doc import centrality_measures as m
from sugarcode.extra_doc.centrality_measures import CentralityError, centrality_measures as run

KEYS = "data keys must be exactly n, edges"
LITERAL_NOT_CLAIMED = [
    "a high score means a node matters",
    "the graph is real",
    "the graph is complete",
    "real-world outcome",
]


def d(n, edges):
    return {"n": n, "edges": [list(e) for e in edges]}


def bad(data, msg):
    with pytest.raises(CentralityError) as e:
        run(data)
    assert str(e.value) == msg


def simple_paths(n, edges, s, t):
    # every simple path s -> t by DFS; shortest ones are filtered by length
    adj = {i: set() for i in range(n)}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    out = []

    def go(path):
        u = path[-1]
        if u == t:
            out.append(list(path))
            return
        for w in sorted(adj[u]):
            if w not in path:
                path.append(w)
                go(path)
                path.pop()
    go([s])
    if not out:
        return []
    best = min(len(p) for p in out)
    return [p for p in out if len(p) == best]


def oracle_between(n, edges):
    res = [Fraction(0)] * n
    for s, t in itertools.combinations(range(n), 2):
        sp = simple_paths(n, edges, s, t)
        for v in range(n):
            if v in (s, t) or not sp:
                continue
            res[v] += Fraction(sum(1 for p in sp if v in p), len(sp))
    return res


def test_path_graph_hand_case():
    out = run(d(4, [[0, 1], [1, 2], [2, 3]]))
    nd = out["nodes"]
    assert [x["degree"] for x in nd] == [1, 2, 2, 1]
    assert [x["degree_centrality"] for x in nd] == ["1/3", "2/3", "2/3", "1/3"]
    assert [x["closeness"] for x in nd] == ["1/2", "3/4", "3/4", "1/2"]
    assert [x["harmonic"] for x in nd] == ["11/6", "5/2", "5/2", "11/6"]
    assert [x["betweenness"] for x in nd] == ["0", "2", "2", "0"]
    assert [x["betweenness_normalized"] for x in nd] == ["0", "2/3", "2/3", "0"]
    assert out["edge_count"] == 3 and out["n"] == 4


def test_star_and_cycle():
    out = run(d(5, [[0, 1], [0, 2], [0, 3], [0, 4]]))
    assert out["nodes"][0]["betweenness"] == "6" and out["nodes"][0]["betweenness_normalized"] == "1"
    assert out["nodes"][0]["closeness"] == "1" and out["nodes"][1]["closeness"] == "4/7"
    # 4-cycle: two shortest paths between opposite nodes, so each node carries 1/2 of one pair
    out = run(d(4, [[0, 1], [1, 2], [2, 3], [3, 0]]))
    assert [x["betweenness"] for x in out["nodes"]] == ["1/2"] * 4


def test_disconnected_and_isolated():
    out = run(d(5, [[0, 1], [1, 2]]))
    nd = out["nodes"]
    assert nd[3]["closeness"] == "0" and nd[3]["harmonic"] == "0" and nd[3]["degree"] == 0
    # node 0 reaches 2 of 4 others at distances 1 and 2: (2/4) * (2/3) = 1/3 ; harmonic 3/2
    assert nd[0]["closeness"] == "1/3" and nd[0]["harmonic"] == "3/2"
    assert nd[1]["betweenness"] == "1" and nd[1]["betweenness_normalized"] == "1/6"
    out = run(d(3, []))
    assert [x["closeness"] for x in out["nodes"]] == ["0"] * 3


def test_betweenness_matches_path_enumeration_oracle():
    graphs = [
        (6, [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [1, 4]]),
        (7, [[0, 1], [0, 2], [1, 3], [2, 3], [3, 4], [4, 5], [4, 6], [5, 6]]),
        (6, [[0, 1], [1, 2], [0, 2], [3, 4]]),
        (5, [[0, 1], [0, 2], [0, 3], [1, 2], [2, 3], [3, 4]]),
    ]
    for n, edges in graphs:
        out = run(d(n, edges))
        ref = oracle_between(n, edges)
        assert [x["betweenness"] for x in out["nodes"]] == [str(v) for v in ref], edges


def test_complete_graph_and_symmetry():
    n = 5
    out = run(d(n, list(itertools.combinations(range(n), 2))))
    for x in out["nodes"]:
        assert x["degree_centrality"] == "1" and x["closeness"] == "1" and x["betweenness"] == "0"
        assert x["harmonic"] == "4"


def test_claims_and_input_not_mutated():
    data = d(4, [[0, 1], [1, 2]])
    before = copy.deepcopy(data)
    out = run(data)
    assert data == before
    assert out["claims"] == {"importance": False, "graph_real": False, "graph_complete": False, "real_world": False}
    out["claims"]["real_world"] = True
    out["not_claimed"].append("x")
    again = run(data)
    assert again["claims"]["real_world"] is False and again["not_claimed"] == LITERAL_NOT_CLAIMED
    assert tuple(again["not_claimed"]) == m.NOT_CLAIMED


def test_constants():
    assert (m.MIN_N, m.MAX_N, m.MAX_EDGES) == (3, 20, 60)


def test_refusals_and_caps():
    for x in (None, [], {"n": 3}, dict(d(3, []), extra=1)):
        bad(x, KEYS)
    for v in (True, 3.0, "3", None):
        bad(d(3, []) | {"n": v}, "n must be an int")
    bad(d(2, []), "n out of range")
    bad(d(21, []), "n out of range")
    run(d(3, []))
    run(d(20, []))
    bad(d(3, []) | {"edges": "ab"}, "edges must be a list")
    pairs = list(itertools.combinations(range(12), 2))
    run(d(12, pairs[:60]))
    bad(d(12, pairs[:61]), "edges length out of range")
    for e in ([0], [0, 1, 2], (0, 1), "ab"):
        bad(d(3, []) | {"edges": [e]}, "edge must be an [a, b] list")
    for v in (True, 1.0, "1"):
        bad(d(3, []) | {"edges": [[v, 1]]}, "node must be an int")
        bad(d(3, []) | {"edges": [[0, v]]}, "node must be an int")
    bad(d(3, [[0, 3]]), "node out of range")
    bad(d(3, [[3, 0]]), "node out of range")
    bad(d(3, [[1, 3]]), "node out of range")
    bad(d(3, [[3, 2]]), "node out of range")
    run(d(3, [[2, 1]]))
    bad(d(3, [[-1, 1]]), "node out of range")
    bad(d(3, [[1, -1]]), "node out of range")
    bad(d(3, [[1, 1]]), "self-loops are not allowed")
    bad(d(3, [[0, 1], [0, 1]]), "duplicate edge")
    bad(d(3, [[0, 1], [1, 0]]), "duplicate edge")
