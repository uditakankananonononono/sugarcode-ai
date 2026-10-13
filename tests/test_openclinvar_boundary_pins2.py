"""Unit 18 v2 pins: endpoints, defaults and exact refusal messages for openclinvar/boundary.py (PARTIAL).
Expected values are hand-derived (Fraction / closed form). Limits are this wrapper's own choices, not spec values.
Illustrative evidence arithmetic only; nothing here is a clinical statement."""
import math
import re
from fractions import Fraction as F

import pytest

from sugarcode.modules.openclinvar import boundary as b
from sugarcode.modules.openclinvar import core

PRE = 10**15


def refuses(exc, msg, fn, *a, **k):
    with pytest.raises(exc, match="^" + re.escape(msg) + "$"):
        fn(*a, **k)


# ---------- _num: types, bool, magnitude endpoints, finiteness (via prior / counts / ages) ----------
def test_num_type_and_bool_messages_exact():
    refuses(TypeError, "prior must be a number, not bool", b.bayesian_acmg_checked, [], True)
    refuses(TypeError, "prior must be a number", b.bayesian_acmg_checked, [], "0.1")
    refuses(TypeError, "prior must be a number", b.bayesian_acmg_checked, [], None)
    refuses(TypeError, "age must be a number", b.forward_trajectory_checked, "pathogenic", 0.5, ["20"])


def test_num_magnitude_endpoints_int_and_float_and_messages():
    # int: exactly 10**15 passes the magnitude cap (then the field's own range refuses it), 10**15+1 is refused by the cap
    refuses(ValueError, "total above allowed range", b.federated_evidence_checked, [{"supporting": 0, "total": PRE}])
    refuses(ValueError, "total magnitude too large", b.federated_evidence_checked, [{"supporting": 0, "total": PRE + 1}])
    refuses(ValueError, "total magnitude too large", b.federated_evidence_checked, [{"supporting": 0, "total": -PRE - 1}])
    # float: exactly 1e15 passes the cap, the next float above is refused by it
    refuses(ValueError, "total above allowed range", b.federated_evidence_checked, [{"supporting": 0, "total": 1e15}])
    refuses(ValueError, "total magnitude too large", b.federated_evidence_checked, [{"supporting": 0, "total": 1.0000000000000002e15}])
    refuses(ValueError, "total magnitude too large", b.federated_evidence_checked, [{"supporting": 0, "total": 1e300}])


def test_num_nonfinite_messages_exact():
    for bad in (float("inf"), float("-inf"), float("nan")):
        refuses(ValueError, "prior must be finite", b.bayesian_acmg_checked, [], bad)
        refuses(ValueError, "penetrance must be finite", b.forward_trajectory_checked, "pathogenic", bad)


def test_num_range_messages_exact_and_open_lower_bound_for_both_priors():
    refuses(ValueError, "prior below allowed range", b.bayesian_acmg_checked, [], 1e-7)
    refuses(ValueError, "prior above allowed range", b.bayesian_acmg_checked, [], 1 - 1e-7)
    b.bayesian_acmg_checked([], 1e-6); b.bayesian_acmg_checked([], 1 - 1e-6)
    refuses(ValueError, "prior_alpha below allowed range", b.federated_evidence_checked, [], 0, 1)
    refuses(ValueError, "prior_beta below allowed range", b.federated_evidence_checked, [], 1, 0)   # beta is open at 0 too
    refuses(ValueError, "prior_beta below allowed range", b.federated_evidence_checked, [], 1, -1)
    refuses(ValueError, "prior_alpha above allowed range", b.federated_evidence_checked, [], 1e12 + 1, 1)
    refuses(ValueError, "prior_beta above allowed range", b.federated_evidence_checked, [], 1, 1e12 + 1)
    assert b.federated_evidence_checked([], 1e12, 1e12)["alpha"] == 1e12


# ---------- containers ----------
def test_container_messages_exact():
    refuses(TypeError, "evidence must be a list or tuple", b.bayesian_acmg_checked, {"strength": "strong"})
    refuses(TypeError, "evidence must be a list or tuple", b.bayesian_acmg_checked, 5)
    refuses(TypeError, "updates must be a list or tuple", b.federated_evidence_checked, "ab")
    refuses(TypeError, "ages must be a list or tuple", b.forward_trajectory_checked, "pathogenic", 0.5, 20)
    refuses(TypeError, "patient_hpo must be a list, tuple or set of text terms", b.phenotype_match_checked, "HP:1", ["HP:1"])
    refuses(TypeError, "disease_hpo must be a list, tuple or set of text terms", b.phenotype_match_checked, ["HP:1"], {"a": 1})
    refuses(TypeError, "evidence[1] must be a mapping", b.bayesian_acmg_checked, [{"strength": "strong"}, 7])
    refuses(TypeError, "evidence[0] must be a mapping", b.bayesian_acmg_checked, [["strength", "strong"]])


def test_cap_messages_exact():
    refuses(ValueError, "evidence exceeds 100 items", b.bayesian_acmg_checked, [{}] * 101)
    assert len(b.bayesian_acmg_checked([{}] * 100)["reasoning_trace"]) == 100
    refuses(ValueError, "ages exceeds 100 items", b.forward_trajectory_checked, "pathogenic", 0.5, [1] * 101)
    assert len(b.forward_trajectory_checked("pathogenic", 0.5, [1] * 100)["ages"]) == 100
    refuses(ValueError, "ages must not be empty", b.forward_trajectory_checked, "pathogenic", 0.5, [])
    refuses(ValueError, "patient_hpo exceeds 1000 terms", b.phenotype_match_checked, [f"t{i}" for i in range(1001)], ["a"])
    assert b.phenotype_match_checked([f"t{i}" for i in range(1000)], ["t0"])["exact_matches"] == 1
    refuses(ValueError, "patient_hpo contains duplicate terms", b.phenotype_match_checked, ["a", "a"], ["a"])
    refuses(TypeError, "patient_hpo term must be non-empty text", b.phenotype_match_checked, ["a", ""], ["a"])
    refuses(TypeError, "disease_hpo term must be non-empty text", b.phenotype_match_checked, ["a"], [3])


# ---------- defaults, hand-computed ----------
def test_bayesian_default_prior_is_one_tenth():
    r = b.bayesian_acmg_checked([])
    assert r["posterior_probability"] == pytest.approx(0.1) and r["prior"] == 0.1 and r["classification"] == "uncertain_significance"
    r = b.bayesian_acmg_checked([{"strength": "strong"}])      # odds = (1/9) * 18.7 ; p = 18.7 / (9 + 18.7)
    assert r["posterior_probability"] == pytest.approx(18.7 / 27.7, rel=1e-12) and r["prior"] == 0.1
    r = b.bayesian_acmg_checked([{"strength": "strong"}], 0.5)
    assert r["posterior_probability"] == pytest.approx(18.7 / 19.7, rel=1e-12)
    r = b.bayesian_acmg_checked([], 0.25)
    assert r["prior"] == 0.25 and isinstance(r["prior"], float)


def test_bayesian_int_priors_0_and_1_are_refused_as_out_of_range():
    refuses(ValueError, "prior above allowed range", b.bayesian_acmg_checked, [], 1)
    refuses(ValueError, "prior below allowed range", b.bayesian_acmg_checked, [], 0)


def test_federated_defaults_alpha_beta_one():
    r = b.federated_evidence_checked([{"supporting": 3, "total": 10}])    # a = 1+3 = 4, b = 1+10-3 = 8, mean = 4/12
    assert (r["alpha"], r["beta"], r["sites"]) == (4, 8, 1) and r["posterior_mean"] == pytest.approx(1 / 3)
    r = b.federated_evidence_checked([])
    assert (r["alpha"], r["beta"], r["posterior_mean"]) == (1, 1, 0.5)
    r = b.federated_evidence_checked([{"supporting": 3, "total": 10}], 2, 3)   # a = 5, b = 3 + 7 = 10
    assert (r["alpha"], r["beta"]) == (5, 10)


def test_federated_update_shape_messages_and_supporting_bounds():
    for bad in ({"supporting": 1}, {"total": 1}, {}, 5, [("supporting", 1), ("total", 2)]):
        refuses(TypeError, "updates[0] needs supporting and total", b.federated_evidence_checked, [bad])
    refuses(TypeError, "updates[2] needs supporting and total", b.federated_evidence_checked,
            [{"supporting": 0, "total": 1}, {"supporting": 0, "total": 1}, {"supporting": 0}])
    refuses(ValueError, "supporting above allowed range", b.federated_evidence_checked, [{"supporting": 4, "total": 3}])
    b.federated_evidence_checked([{"supporting": 3, "total": 3}])


def test_forward_trajectory_defaults_penetrance_half_ages_20_40_60():
    r = b.forward_trajectory_checked("pathogenic")
    assert r["ages"] == [20, 40, 60] and r["assumptions"]["penetrance"] == 0.5
    for a, got in zip((20, 40, 60), r["cumulative_risk"]):
        assert got == pytest.approx(0.5 * (1 - math.exp(-a / 45)), rel=1e-12)
    r = b.forward_trajectory_checked("likely_benign", 0.8, (45,))        # 0.8 * 0.1 * (1 - e^-1)
    assert r["cumulative_risk"] == [pytest.approx(0.08 * (1 - math.exp(-1)), rel=1e-12)]
    refuses(ValueError, "classification must be one of " + repr(b.CLASSES), b.forward_trajectory_checked, "nope")
    refuses(ValueError, "classification must be one of " + repr(b.CLASSES), b.forward_trajectory_checked, 3)
    refuses(ValueError, "age above allowed range", b.forward_trajectory_checked, "pathogenic", 0.5, [120.0001])
    b.forward_trajectory_checked("pathogenic", 0.5, [0, 120])
    refuses(ValueError, "age below allowed range", b.forward_trajectory_checked, "pathogenic", 0.5, [-0.0001])
    refuses(ValueError, "penetrance above allowed range", b.forward_trajectory_checked, "pathogenic", 1.0001)
    b.forward_trajectory_checked("pathogenic", 1.0); b.forward_trajectory_checked("pathogenic", 0.0)


# ---------- evidence_consensus: years and fields ----------
def rec(**k):
    return [{"classification": "pathogenic", **k}]


def test_year_endpoints_and_messages():
    for y in (1900, 2026):
        assert b.evidence_consensus_checked(rec(year=y))["consensus"] == "pathogenic"
    for y in (1899, 2027, 0, -5, 3800):
        refuses(ValueError, "year must be between 1900 and 2026", b.evidence_consensus_checked, rec(year=y))
    for y in (2000.0, "2000", True, None):
        refuses(TypeError, "year must be an integer", b.evidence_consensus_checked, rec(year=y))
    # hand-computed weight for year 2016, quality .5 default, sample 1: recency = 1/(1+10/10) = .5 ; sample = ln2/5
    r = b.evidence_consensus_checked(rec(year=2016))
    w = 0.5 * (0.5 + 0.3 * 0.5 + 0.2 * min(1, math.log1p(1) / 5))
    assert r["effective_support"] == pytest.approx(w, rel=1e-12)


def test_consensus_field_messages_and_bounds():
    refuses(TypeError, "records[1] must be a mapping", b.evidence_consensus_checked, rec() + ["x"])
    refuses(TypeError, "classification must be non-empty text", b.evidence_consensus_checked, [{"quality": 1}])
    refuses(TypeError, "classification must be non-empty text", b.evidence_consensus_checked, [{"classification": ""}])
    refuses(ValueError, "quality above allowed range", b.evidence_consensus_checked, rec(quality=1.0001))
    refuses(ValueError, "quality below allowed range", b.evidence_consensus_checked, rec(quality=-0.0001))
    b.evidence_consensus_checked(rec(quality=1.0)); b.evidence_consensus_checked(rec(quality=0.0))
    refuses(ValueError, "sample_size above allowed range", b.evidence_consensus_checked, rec(sample_size=1e12 + 1))
    refuses(ValueError, "sample_size below allowed range", b.evidence_consensus_checked, rec(sample_size=-1))
    b.evidence_consensus_checked(rec(sample_size=1e12)); b.evidence_consensus_checked(rec(sample_size=0))


# ---------- reverse_inference / graph ----------
def test_variant_probability_endpoints_and_messages():
    cand = lambda p: [{"phenotypes": ["a"], "variant_probability": p}]
    b.reverse_inference_checked(["a"], cand(1.0)); b.reverse_inference_checked(["a"], cand(0.0))
    for bad in (1.0000001, 2.0, 5):
        refuses(ValueError, "variant_probability above allowed range", b.reverse_inference_checked, ["a"], cand(bad))
    refuses(ValueError, "variant_probability below allowed range", b.reverse_inference_checked, ["a"], cand(-0.1))
    # 1.0 reaches core: score = .65 * 1 + .35 * 1.0 = 1.0
    assert b.reverse_inference_checked(["a"], cand(1.0))[0]["diagnostic_score"] == pytest.approx(1.0)
    refuses(TypeError, "candidates[0] must be a mapping", b.reverse_inference_checked, ["a"], ["a"])
    refuses(TypeError, "candidate phenotypes must be a list, tuple or set of text terms", b.reverse_inference_checked, ["a"], [{"phenotypes": "ab"}])


def test_ancestor_map_and_graph_messages_exact():
    refuses(TypeError, "ancestor_map must be a mapping", b.phenotype_match_checked, ["a"], ["b"], [("a", ["b"])])
    refuses(TypeError, "ancestor_map key must be non-empty text", b.phenotype_match_checked, ["a"], ["b"], {"": ["b"]})
    refuses(TypeError, "ancestor_map values must be collections of text", b.phenotype_match_checked, ["a"], ["b"], {"a": "b"})
    refuses(TypeError, "ancestor_map term must be non-empty text", b.phenotype_match_checked, ["a"], ["b"], {"a": [1]})
    assert b.phenotype_match_checked(["a"], ["b"], {"a": ["b"]})["semantic_partial"] == 0.5
    refuses(ValueError, "graph node ids must be unique", b.reasoning_graph_checked, "g", "v", "c", ["x"], ["x"])
    refuses(ValueError, "graph node ids must be unique", b.reasoning_graph_checked, "g", "g", "c")
    refuses(ValueError, "graph node ids must be unique", b.reasoning_graph_checked, "g", "v", "c", structure_effect="c")
    refuses(TypeError, "structure_effect must be non-empty text", b.reasoning_graph_checked, "g", "v", "c", structure_effect="")
    refuses(TypeError, "variant must be non-empty text", b.reasoning_graph_checked, "g", "", "c")
    refuses(TypeError, "gene must be non-empty text", b.reasoning_graph_checked, "", "v", "c")
    refuses(TypeError, "consequence must be non-empty text", b.reasoning_graph_checked, "g", "v", "")
