"""Unit 18 (OpenClinVar) input-boundary tests. Oracles: Fraction / independent formulas.
Illustrative evidence arithmetic only; nothing here is a clinical statement."""
import math
from fractions import Fraction as F

import pytest

from sugarcode.modules.openclinvar import core
from sugarcode.modules.openclinvar.boundary import (
    bayesian_acmg_checked, evidence_consensus_checked, federated_evidence_checked,
    forward_trajectory_checked, phenotype_match_checked, reasoning_graph_checked,
    reverse_inference_checked,
)

BAD = (TypeError, ValueError)


def test_core_defects_documented():
    assert math.isnan(core.bayesian_acmg([{"strength": "very_strong"}] * 200)["posterior_probability"])
    assert core.federated_evidence([{"supporting": 10, "total": 3}])["posterior_mean"] > 1
    assert min(core.forward_trajectory("pathogenic", -3)["cumulative_risk"]) < 0
    assert core.evidence_consensus([{"classification": "b", "quality": -1}])["effective_support"] < 0
    assert core.phenotype_match("HP:1", "HP:1")["exact_matches"] == 4
    assert core.bayesian_acmg([{"strength": "bogus"}])["posterior_probability"] == pytest.approx(0.1)


# ---- bayesian_acmg ----
LR = {"very_strong": F(350), "strong": F("18.7"), "moderate": F("4.3"), "supporting": F("2.08")}


def _bayes_oracle(ev, prior):
    odds = F(prior) / (1 - F(prior))
    for e in ev:
        lr = LR[e.get("strength", "supporting")]
        odds *= lr if e.get("direction", "pathogenic") == "pathogenic" else 1 / lr
    return float(odds / (1 + odds))


@pytest.mark.parametrize("ev,prior", [
    ([], 0.1), ([{"strength": "strong"}], 0.1), ([{"strength": "very_strong"}, {"strength": "moderate", "direction": "benign"}], 0.25),
    ([{}], 0.5), ([{"strength": "supporting", "direction": "benign"}] * 5, 0.01),
    ([{"strength": "very_strong"}] * 100, 0.1),
])
def test_bayes_matches_fraction_oracle(ev, prior):
    r = bayesian_acmg_checked(ev, prior)
    assert r["posterior_probability"] == pytest.approx(_bayes_oracle(ev, prior), rel=1e-9, abs=1e-300)
    assert 0 <= r["posterior_probability"] <= 1
    assert r["prior"] == prior


@pytest.mark.parametrize("ev,prior", [
    ([{"strength": "very_strong"}] * 101, 0.1),                  # cap, would overflow in core
    ([{"strength": "bogus"}], 0.1), ([{"direction": "patho"}], 0.1),
    ([{"strength": None}], 0.1), (["strong"], 0.1), ("strong", 0.1), (None, 0.1),
    ({"strength": "strong"}, 0.1),
    ([], True), ([], 0), ([], 1), ([], float("nan")), ([], 1e-7), ([], 1 - 1e-7), ([], "0.1"), ([], 10**400),
])
def test_bayes_rejects(ev, prior):
    with pytest.raises(BAD):
        bayesian_acmg_checked(ev, prior)


def test_bayes_cap_accepts_exactly_100_and_prior_bounds():
    bayesian_acmg_checked([{}] * 100, 0.5)
    bayesian_acmg_checked([], 1e-6)
    bayesian_acmg_checked([], 1 - 1e-6)


# ---- federated_evidence ----
def _fed_oracle(ups, a0, b0):
    s = sum(F(u["supporting"]) for u in ups); t = sum(F(u["total"]) for u in ups)
    a = F(a0) + s; b = F(b0) + t - s
    return float(a), float(b), float(a / (a + b))


@pytest.mark.parametrize("ups,a0,b0", [
    ([], 1, 1), ([{"supporting": 3, "total": 10}], 1, 1), ([{"supporting": 0, "total": 0}], 1, 1),
    ([{"supporting": 2, "total": 4}, {"supporting": 7, "total": 9}], 0.5, 2.5),
    ([{"supporting": 5, "total": 5}], 2, 2), ([{"supporting": 1.5, "total": 3.25}], 1, 1),
])
def test_fed_matches_oracle(ups, a0, b0):
    r = federated_evidence_checked(ups, a0, b0)
    a, b, m = _fed_oracle(ups, a0, b0)
    assert (r["alpha"], r["beta"]) == (pytest.approx(a), pytest.approx(b))
    assert r["posterior_mean"] == pytest.approx(m) and 0 < r["posterior_mean"] < 1
    assert r["sites"] == len(ups)


@pytest.mark.parametrize("ups,a0,b0", [
    ([{"supporting": 10, "total": 3}], 1, 1), ([{"supporting": -5, "total": -5}], 1, 1),
    ([{"supporting": -1, "total": 5}], 1, 1), ([{"supporting": float("nan"), "total": 3}], 1, 1),
    ([{"supporting": 1, "total": float("inf")}], 1, 1), ([{"supporting": True, "total": 3}], 1, 1),
    ([{"supporting": 1, "total": 10**13}], 1, 1), ([{"supporting": 1, "total": 10**400}], 1, 1),
    ([{"supporting": 1}], 1, 1), ([{"supporting": "1", "total": 3}], 1, 1), (["x"], 1, 1),
    ([], 0, 0), ([], 0, 1), ([], 1, -1), ([], True, 1), ([], float("nan"), 1), ([], 1, 10**13),
    (None, 1, 1), ({"supporting": 1, "total": 2}, 1, 1),
    ([{"supporting": 0, "total": 0}] * 10_001, 1, 1),
])
def test_fed_rejects(ups, a0, b0):
    with pytest.raises(BAD):
        federated_evidence_checked(ups, a0, b0)


def test_fed_site_cap_boundary():
    assert federated_evidence_checked([{"supporting": 0, "total": 0}] * 10_000)["sites"] == 10_000
    r = federated_evidence_checked([{"supporting": 10**12, "total": 10**12}])
    assert 0 < r["posterior_mean"] < 1


# ---- forward_trajectory ----
@pytest.mark.parametrize("cls,pen,ages", [
    ("pathogenic", 0.5, (20, 40, 60)), ("benign", 1.0, (0,)), ("likely_pathogenic", 0.0, [10, 30]),
    ("uncertain_significance", 0.3, (120,)), ("likely_benign", 0.9, (45.5,)),
])
def test_traj_matches_independent_formula(cls, pen, ages):
    f = {"pathogenic": 1, "likely_pathogenic": .75, "uncertain_significance": .35, "likely_benign": .1, "benign": .02}[cls]
    r = forward_trajectory_checked(cls, pen, ages)
    assert r["cumulative_risk"] == pytest.approx([pen * f * (1 - math.exp(-a / 45)) for a in ages])
    assert all(0 <= x <= 1 for x in r["cumulative_risk"])
    assert r["ages"] == list(ages)


@pytest.mark.parametrize("cls,pen,ages", [
    ("pathogenic", -3, (20,)), ("pathogenic", 5, (20,)), ("pathogenic", 1.0000001, (20,)),
    ("pathogenic", True, (20,)), ("pathogenic", float("nan"), (20,)), ("pathogenic", 10**400, (20,)),
    ("pathogenic", .5, (-10,)), ("pathogenic", .5, (121,)), ("pathogenic", .5, ()), ("pathogenic", .5, (True,)),
    ("pathogenic", .5, (float("nan"),)), ("pathogenic", .5, "20"), ("pathogenic", .5, (20,) * 101),
    ("pathogenic", .5, None), ("bogus", .5, (20,)), (None, .5, (20,)), ("Pathogenic", .5, (20,)),
])
def test_traj_rejects(cls, pen, ages):
    with pytest.raises(BAD):
        forward_trajectory_checked(cls, pen, ages)


def test_traj_cap_boundary():
    assert len(forward_trajectory_checked("benign", 0.5, (20,) * 100)["cumulative_risk"]) == 100
    forward_trajectory_checked("benign", 0.0, (0,)); forward_trajectory_checked("benign", 1, (120,))


# ---- evidence_consensus ----
def _w(r):
    q = F(str(r.get("quality", .5))); y = int(r.get("year", 2026)); s = r.get("sample_size", 1)
    rec = 1 / (1 + F(max(0, 2026 - y)) / 10); smp = min(1.0, math.log1p(float(s)) / 5)
    return float(q) * (.5 + .3 * float(rec) + .2 * smp)


def test_consensus_matches_independent_weights():
    recs = [{"classification": "a", "quality": .9, "year": 2020, "sample_size": 100},
            {"classification": "b", "quality": .4, "year": 2026, "sample_size": 5},
            {"classification": "a", "quality": 1, "year": 1900, "sample_size": 0}]
    r = evidence_consensus_checked(recs)
    exp = {"a": _w(recs[0]) + _w(recs[2]), "b": _w(recs[1])}
    assert r["weighted_votes"] == pytest.approx(exp)
    assert r["consensus"] == "a" and len(r["conflicts"]) == 1
    assert r["effective_support"] == pytest.approx(sum(exp.values()))
    assert all(x["evidence_weight"] >= 0 for x in r["records"])


def test_consensus_empty_ok():
    assert evidence_consensus_checked([])["consensus"] is None


@pytest.mark.parametrize("rec", [
    {"classification": "a", "quality": -1}, {"classification": "a", "quality": 1.5},
    {"classification": "a", "quality": True}, {"classification": "a", "quality": float("nan")},
    {"classification": "a", "sample_size": -5}, {"classification": "a", "sample_size": 10**13},
    {"classification": "a", "sample_size": float("inf")}, {"classification": "a", "sample_size": 10**400},
    {"classification": "a", "year": 2100}, {"classification": "a", "year": 1899}, {"classification": "a", "year": True},
    {"classification": "a", "year": 2020.5}, {"classification": "a", "year": "2020"},
    {"classification": ""}, {"classification": 5}, {"classification": ["a"]}, {}, "a",
])
def test_consensus_rejects(rec):
    with pytest.raises(BAD):
        evidence_consensus_checked([rec])


def test_consensus_container_and_cap():
    for bad in (None, "x", {"classification": "a"}):
        with pytest.raises(BAD):
            evidence_consensus_checked(bad)
    ok = [{"classification": "a"}] * 10_000
    assert len(evidence_consensus_checked(ok)["records"]) == 10_000
    with pytest.raises(ValueError):
        evidence_consensus_checked(ok + [{"classification": "a"}])
    r = evidence_consensus_checked([{"classification": "a", "quality": 0, "year": 2026, "sample_size": 0},
                                    {"classification": "a", "quality": 1, "year": 1900, "sample_size": 10**12}])
    assert r["effective_support"] > 0


# ---- phenotype_match / reverse_inference ----
def test_phenotype_match_oracle():
    p, d = ["HP:1", "HP:2", "HP:3"], ["HP:2", "HP:3", "HP:9"]
    r = phenotype_match_checked(p, d, {"HP:1": ["HP:9"]})
    assert r["exact_matches"] == 2 and r["semantic_partial"] == 0.5
    assert r["score"] == pytest.approx(min(1.0, (2 + .5) / len(set(p) | set(d))))
    assert phenotype_match_checked((), ())["score"] == 0


@pytest.mark.parametrize("p,d,anc", [
    ("HP:1", ["HP:1"], None), (["HP:1"], "HP:1", None), (["HP:1", "HP:1"], ["HP:1"], None),
    (["HP:1"], ["HP:1", "HP:1"], None), ([""], ["HP:1"], None), ([1], ["HP:1"], None),
    (None, [], None), ([], None, None), (["HP:1"], ["HP:2"], {"HP:1": "HP:2"}), (["HP:1"], ["HP:2"], [("HP:1", ["HP:2"])]),
    (["HP:1"], ["HP:2"], {1: ["HP:2"]}), (["HP:1"], ["HP:2"], {"HP:1": [2]}),
    ([f"HP:{i}" for i in range(1001)], [], None),
])
def test_phenotype_match_rejects(p, d, anc):
    with pytest.raises(BAD):
        phenotype_match_checked(p, d, anc)


def test_phenotype_set_inputs_accepted_and_cap():
    assert phenotype_match_checked({"a"}, frozenset({"a"}))["exact_matches"] == 1
    phenotype_match_checked([f"HP:{i}" for i in range(1000)], [])


def test_reverse_inference_oracle_and_rejects():
    cands = [{"name": "x", "phenotypes": ["a", "b"], "variant_probability": .2},
             {"name": "y", "phenotypes": ["a"], "variant_probability": 1.0}]
    r = reverse_inference_checked(["a", "b"], cands)
    exp = {"x": .65 * 1.0 + .35 * .2, "y": .65 * (1 / 2) + .35 * 1.0}
    assert {c["name"]: c["diagnostic_score"] for c in r} == pytest.approx(exp)
    assert [c["name"] for c in r] == sorted(exp, key=lambda k: -exp[k])
    for bad in ({"variant_probability": 5}, {"variant_probability": -.1}, {"variant_probability": True},
                {"variant_probability": float("nan")}, {"phenotypes": "abc"}, {"phenotypes": ["a", "a"]}):
        with pytest.raises(BAD):
            reverse_inference_checked(["a"], [bad])
    for bad in (None, "x", [1], {"a": 1}):
        with pytest.raises(BAD):
            reverse_inference_checked(["a"], bad)
    assert reverse_inference_checked(["a"], []) == []
    with pytest.raises(ValueError):
        reverse_inference_checked(["a"], [{}] * 10_001)


# ---- reasoning_graph ----
def test_graph_matches_expected_structure():
    g = reasoning_graph_checked("G", "v", "missense", ["h1", "h2"], ["p1"], "fold")
    ids = [n["id"] for n in g["nodes"]]
    assert ids == ["v", "G", "missense", "p1", "h1", "h2", "fold"] and len(set(ids)) == len(ids)
    assert g["causal_chain"] == ["v", "missense", "p1", "h1", "h2"]
    assert len(g["edges"]) == 2 + 1 + 2 + 1


@pytest.mark.parametrize("args", [
    ("G", "v", "m", "abc", ()), ("G", "v", "m", (), "abc"), ("G", "v", "m", ["h", "h"], ()), ("G", "v", "m", (), ["p", "p"]),
    ("G", "v", "m", ["x"], ["x"]), ("G", "G", "m", (), ()), ("G", "v", "v", (), ()), ("G", "v", "m", ["v"], ()),
    ("", "v", "m", (), ()), ("G", "", "m", (), ()), ("G", "v", "", (), ()), (None, "v", "m", (), ()),
    ("G", "v", "m", [1], ()), ("G", "v", "m", (), [None]), ("G", "v", "m", None, ()),
    ("G", "v", "m", [f"h{i}" for i in range(1001)], ()),
])
def test_graph_rejects(args):
    with pytest.raises(BAD):
        reasoning_graph_checked(*args)


def test_graph_structure_effect_validation():
    for bad in (5, "", ["x"]):
        with pytest.raises(BAD):
            reasoning_graph_checked("G", "v", "m", (), (), bad)
    with pytest.raises(ValueError):
        reasoning_graph_checked("G", "v", "m", (), (), "G")
    reasoning_graph_checked("G", "v", "m", [f"h{i}" for i in range(1000)], [f"p{i}" for i in range(1000)])
