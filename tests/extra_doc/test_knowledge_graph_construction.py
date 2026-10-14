import copy
import itertools
import random

import pytest

from sugarcode.extra_doc import knowledge_graph_construction as m
from sugarcode.extra_doc.knowledge_graph_construction import KgError, knowledge_graph_construction as run

KEYS = "data keys must be exactly triples, rules"
NAME = "name must be 1..30 characters from a-z, 0-9 and underscore"
TR = [["ann", "parent_of", "bob"], ["bob", "parent_of", "cy"], ["ann", "knows", "dee"]]
RU = [["parent_of", "transitive", None], ["knows", "symmetric", None], ["parent_of", "inverse", "child_of"]]


def d(tr=None, ru=None):
    return {"triples": [list(t) for t in (TR if tr is None else tr)],
            "rules": [list(r) for r in (RU if ru is None else ru)]}


def bad(data, msg):
    with pytest.raises(KgError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(data):
    """Independent: naive fixpoint by joining the whole edge list against itself each round."""
    stated = {tuple(t) for t in data["triples"]}
    E = set(stated)
    while True:
        add = set()
        for (a, p, b), (c, q, e) in itertools.product(E, E):
            for rp, kind, other in data["rules"]:
                if kind == "transitive" and p == q == rp and b == c:
                    add.add((a, rp, e))
        for (a, p, b) in E:
            for rp, kind, other in data["rules"]:
                if kind == "symmetric" and p == rp:
                    add.add((b, rp, a))
                if kind == "inverse" and p == rp:
                    add.add((b, other, a))
                if kind == "inverse" and p == other:
                    add.add((b, rp, a))
        if add <= E:
            break
        E |= add
    nodes = sorted({x for a, _, b in E for x in (a, b)})
    comp = {n: {n} for n in nodes}
    for a, _, b in E:
        u = comp[a] | comp[b]
        for x in u:
            comp[x] = u
    ncomp = len({frozenset(v) for v in comp.values()})
    return stated, E, nodes, ncomp


def check(data):
    out = run(data)
    stated, E, nodes, ncomp = oracle(data)
    assert out["nodes"] == nodes
    assert {(s, p, o) for s, p, o, _ in out["edges"]} == E and len(out["edges"]) == len(E)
    assert out["edges"] == sorted(out["edges"])
    for s, p, o, tag in out["edges"]:
        assert tag == ("stated" if (s, p, o) in stated else "inferred")
    assert out["stated_edges"] == len(stated) and out["inferred_edges"] == len(E) - len(stated)
    assert out["out_degree"] == {n: sum(1 for s, _, _ in E if s == n) for n in nodes}
    assert out["in_degree"] == {n: sum(1 for _, _, o in E if o == n) for n in nodes}
    assert out["components"] == ncomp
    return out


def test_basic_closure():
    out = check(d())
    es = {(s, p, o): t for s, p, o, t in out["edges"]}
    assert es[("ann", "parent_of", "cy")] == "inferred"
    assert es[("dee", "knows", "ann")] == "inferred"
    assert es[("cy", "child_of", "bob")] == "inferred" and es[("bob", "child_of", "ann")] == "inferred"
    assert es[("cy", "child_of", "ann")] == "inferred"
    assert es[("ann", "parent_of", "bob")] == "stated"
    assert out["stated_edges"] == 3 and out["inferred_edges"] == 5 and out["components"] == 1
    assert out["status"] == "completed"
    assert out["claims"] == {"truth": False, "rules_valid": False, "complete": False, "real_world": False}
    assert len(out["not_claimed"]) == 4


def test_each_rule_alone():
    out = check(d([["a", "p", "b"]], [["p", "symmetric", None]]))
    assert out["inferred_edges"] == 1
    out = check(d([["a", "p", "b"]], [["p", "inverse", "q"]]))
    assert [e[:3] for e in out["edges"]] == [["a", "p", "b"], ["b", "q", "a"]]
    out = check(d([["a", "q", "b"]], [["p", "inverse", "q"]]))
    assert [e[:3] for e in out["edges"]] == [["a", "q", "b"], ["b", "p", "a"]]
    out = check(d([["a", "p", "b"], ["b", "p", "c"], ["c", "p", "d"]], [["p", "transitive", None]]))
    assert out["inferred_edges"] == 3 and len(out["edges"]) == 6
    out = check(d([["a", "p", "b"], ["b", "q", "c"]], [["p", "transitive", None]]))
    assert out["inferred_edges"] == 0
    out = check(d([["a", "p", "b"], ["b", "p", "c"]], []))
    assert out["inferred_edges"] == 0


def test_rule_interaction_and_cycles():
    out = check(d([["a", "p", "b"], ["b", "p", "c"], ["c", "p", "a"]], [["p", "transitive", None]]))
    assert len(out["edges"]) == 9 and out["inferred_edges"] == 6
    out = check(d([["a", "p", "a"]], [["p", "transitive", None], ["p", "symmetric", None]]))
    assert len(out["edges"]) == 1 and out["inferred_edges"] == 0
    out = check(d([["a", "p", "b"], ["b", "p", "c"]], [["p", "symmetric", None], ["p", "transitive", None]]))
    assert len(out["edges"]) == 9      # symmetric + transitive gives the full relation on {a,b,c}
    out = check(d([["a", "p", "b"]], [["p", "inverse", "q"], ["q", "transitive", None], ["q", "symmetric", None]]))
    assert len(out["edges"]) >= 3


def test_duplicates_collapsed_and_components_and_degrees():
    out = check(d([["a", "p", "b"], ["a", "p", "b"], ["x", "p", "y"], ["a", "q", "b"]], []))
    assert out["stated_edges"] == 3 and out["components"] == 2
    assert out["out_degree"] == {"a": 2, "b": 0, "x": 1, "y": 0}
    assert out["in_degree"] == {"a": 0, "b": 2, "x": 0, "y": 1}
    out = check(d([["a", "p", "a"]], []))
    assert out["components"] == 1 and out["out_degree"] == {"a": 1} and out["in_degree"] == {"a": 1}


def test_random_against_oracle():
    rng = random.Random(41)
    nodes = ["a", "b", "c", "d", "e"]
    preds = ["p", "q", "r"]
    for _ in range(300):
        tr = [[rng.choice(nodes), rng.choice(preds), rng.choice(nodes)] for _ in range(rng.randint(1, 7))]
        pool = [["p", "transitive", None], ["q", "symmetric", None], ["p", "inverse", "r"], ["r", "transitive", None],
                ["q", "inverse", "p"], ["r", "symmetric", None]]
        ru = rng.sample(pool, rng.randint(0, 4))
        check(d(tr, ru))


def test_name_rules():
    run(d([["a" * 30, "p", "b"]], []))
    run(d([["a_0z9", "p_", "_9"]], []))
    for bad_name in ["a" * 31, "", "Ab", "a b", "a-b", "a.b", "\u00e9", "a\n"]:
        bad(d([[bad_name, "p", "b"]], []), NAME)
        bad(d([["a", bad_name, "b"]], []), NAME)
        bad(d([["a", "p", bad_name]], []), NAME)
        bad(d([["a", "p", "b"]], [[bad_name, "symmetric", None]]), NAME)
        bad(d([["a", "p", "b"]], [["p", "inverse", bad_name]]), NAME)


def test_rule_validation():
    bad(d(ru=[["parent_of", "reflexive", None]]), "rule kind must be symmetric, transitive or inverse")
    for k in [True, 1, None, [], "Symmetric", "symmetric "]:
        bad(d(ru=[["p", k, None]]), "rule kind must be symmetric, transitive or inverse")
    bad(d(ru=[["p", "symmetric", "q"]]), "other must be None unless kind is inverse")
    bad(d(ru=[["p", "transitive", ""]]), "other must be None unless kind is inverse")
    bad(d(ru=[["p", "inverse", None]]), "inverse predicate must be a string")
    bad(d(ru=[["p", "inverse", 1]]), "inverse predicate must be a string")
    bad(d(ru=[["p", "inverse", "p"]]), "inverse predicate must differ from the rule predicate")
    bad(d(ru=[["p", "symmetric", None], ["p", "symmetric", None]]), "rules must be distinct")
    run(d(ru=[["p", "symmetric", None], ["p", "transitive", None], ["p", "inverse", "q"], ["p", "inverse", "r"]]))
    bad(d(ru=[["p"]]), "rule must be [predicate, kind, other]")
    bad(d(ru=[["p", "symmetric", None, 1]]), "rule must be [predicate, kind, other]")
    x = d()
    x["rules"] = [5]
    bad(x, "rule must be [predicate, kind, other]")
    x["rules"] = [["p", "inverse", ["q"]]]
    bad(x, "inverse predicate must be a string")


def test_caps_and_boundaries():
    run(d([["a%d" % (i % 40), "p", "a%d" % ((i + 1) % 40)] for i in range(100)], []))
    bad(d([["a", "p", "b"]] * 101, []), "triples must be a list of 1..100 [subject, predicate, object]")
    bad(d([["a", "p", "b"]] * 10**5, []), "triples must be a list of 1..100 [subject, predicate, object]")
    bad(d([], []), "triples must be a list of 1..100 [subject, predicate, object]")
    run(d([["n%d" % i, "p", "n%d" % (i + 1)] for i in range(39)], []))              # 40 nodes
    bad(d([["n%d" % i, "p", "n%d" % (i + 1)] for i in range(40)], []), "too many distinct nodes")
    run(d(ru=[["r%d" % i, "symmetric", None] for i in range(10)]))
    bad(d(ru=[["r%d" % i, "symmetric", None] for i in range(11)]), "rules must be a list of 0..10 rules")
    bad(d(ru=[["r", "symmetric", None]] * 10**5), "rules must be a list of 0..10 rules")


def _cap_case(extra):
    # p-cycle over 30 nodes (900 edges after transitivity) + its inverse q (900),
    # r-cycle over 40 nodes (1600) + its inverse s (1600): exactly 5000 closed edges
    tr = [["n%d" % i, "p", "n%d" % ((i + 1) % 30)] for i in range(30)]
    tr += [["n%d" % i, "r", "n%d" % ((i + 1) % 40)] for i in range(40)]
    tr += [["n0", "u%d" % i, "n1"] for i in range(extra)]
    ru = [["p", "transitive", None], ["p", "inverse", "q"], ["r", "transitive", None], ["r", "inverse", "s"]]
    return d(tr, ru)


def test_edge_cap_boundary_exact():
    out = run(_cap_case(0))
    assert len(out["edges"]) == 5000 and out["stated_edges"] == 70
    bad(_cap_case(1), "closure exceeds 5000 edges")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, [], {}, b"a"])
def test_nonstring_slots(v):
    bad(d([[v, "p", "b"]], []), "subject must be a string")
    bad(d([["a", v, "b"]], []), "predicate must be a string")
    bad(d([["a", "p", v]], []), "object must be a string")
    bad(d(ru=[[v, "symmetric", None]]), "rule predicate must be a string")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "ab", {}, ("a", "b", "c")])
def test_noncontainer(v):
    x = d()
    x["triples"] = v
    bad(x, "triples must be a list of 1..100 [subject, predicate, object]")
    x = d()
    x["rules"] = v
    bad(x, "rules must be a list of 0..10 rules")
    x = d()
    x["triples"] = [v]
    bad(x, "triple must be [subject, predicate, object]")
    for t in (["a", "p"], ["a", "p", "b", "c"]):
        x = d()
        x["triples"] = [t]
        bad(x, "triple must be [subject, predicate, object]")


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("triples", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    for k in ("triples", "rules"):
        x = d()
        del x[k]
        bad(x, KEYS)
        x["other"] = 1
        bad(x, KEYS)
    x = d()
    x["extra"] = 1
    bad(x, KEYS)


def test_no_mutation_determinism_fresh_claims():
    x = d()
    y = copy.deepcopy(x)
    a, b = run(x), run(x)
    assert x == y and a == b
    a["claims"]["truth"] = True
    a["edges"][0][0] = "zz"
    a["out_degree"]["ann"] = 99
    r = run(x)
    assert r["claims"]["truth"] is False and r["edges"][0][0] != "zz" and r["out_degree"]["ann"] != 99
    assert m.CLAIMS["truth"] is False
