"""Unit 18 0004: prior floor, interior-posterior guarantee, and ancestor/pair caps (PARTIAL).
Caps and floor are this wrapper's own choices (MIN_PRIOR 1e-6, MAX_ANCESTOR_KEYS 1000, MAX_ANCESTORS_PER_KEY 100,
MAX_ANCESTOR_TERMS 10000, MAX_PAIRS 100000), not spec values. Illustrative evidence arithmetic only."""
import re
import time
from fractions import Fraction as F

import pytest

from sugarcode.modules.openclinvar import boundary as b
from sugarcode.modules.openclinvar import core


def refuses(exc, msg, fn, *a, **k):
    with pytest.raises(exc, match="^" + re.escape(msg) + "$"):
        fn(*a, **k)


# ---------------- (1) prior floor and interior posterior ----------------
def test_auditor_case_tiny_beta_prior_now_refused_and_core_defect_documented():
    upd = [{"supporting": 1, "total": 1}]
    core_out = core.federated_evidence(upd, 1, 1e-20)           # the defect: 1e-20 + 1 - 1 cancels to 0, mean exactly 1
    assert core_out["beta"] == 0 and core_out["posterior_mean"] == 1
    refuses(ValueError, "prior_beta below allowed range", b.federated_evidence_checked, upd, 1, 1e-20)
    refuses(ValueError, "prior_alpha below allowed range", b.federated_evidence_checked, upd, 1e-20, 1)


def test_prior_floor_endpoints_and_interior_result_hand_computed():
    upd = [{"supporting": 1, "total": 1}]
    refuses(ValueError, "prior_beta below allowed range", b.federated_evidence_checked, upd, 1, 9.99e-7)
    r = b.federated_evidence_checked(upd, 1, 1e-6)              # a = 2, b = 1e-6 + 1 - 1 (float) ~ 1e-6: mean = 2/(2+1e-6)
    assert 0 < r["beta"] < 1e-5 and r["beta"] == pytest.approx(1e-6, rel=1e-3)
    assert r["posterior_mean"] == pytest.approx(float(F(2) / (F(2) + F(1, 10**6))), rel=1e-9) and r["posterior_mean"] < 1
    r = b.federated_evidence_checked(upd, 1e-6, 1)              # a = 1 + 1e-6, b = 1: mean = a/(a+1)
    assert r["alpha"] == pytest.approx(1 + 1e-6) and r["posterior_mean"] == pytest.approx((1 + 1e-6) / (2 + 1e-6), rel=1e-12)


def test_float_cancellation_at_large_counts_is_refused_not_returned_as_beta_zero():
    # 1e-6 + 1e12 rounds to 1e12 (ulp 1.2e-4), so beta = 1e-6 + 1e12 - 1e12 = 0 in floats although the exact beta is 1e-6
    upd = [{"supporting": 1e12, "total": 1e12}]
    assert core.federated_evidence(upd, 1, 1e-6)["beta"] == 0
    refuses(ValueError, "posterior is not interior: beta or mean degenerate after float cancellation",
            b.federated_evidence_checked, upd, 1, 1e-6)
    r = b.federated_evidence_checked(upd, 1, 1)                 # beta = 1 exactly, a = 1e12 + 1, mean = a/(a+1) < 1
    assert r["beta"] == 1 and 0 < r["posterior_mean"] < 1
    assert r["posterior_mean"] == pytest.approx(float(F(10**12 + 1, 10**12 + 2)), rel=1e-15)


def test_every_accepted_federated_input_has_interior_posterior_sweep():
    # independent exact-arithmetic oracle: whenever the wrapper returns, the exact posterior is interior and the float one agrees
    for a0 in (1e-6, 0.5, 1, 1e6):
        for b0 in (1e-6, 0.5, 1, 1e6):
            for s, t in ((0, 0), (0, 5), (3, 5), (5, 5), (1e6, 1e6), (1e9, 1e9), (1e12, 1e12), (0, 1e12)):
                try:
                    r = b.federated_evidence_checked([{"supporting": s, "total": t}], a0, b0)
                except ValueError:
                    continue
                ea, eb = F(a0) + F(s), F(b0) + F(t) - F(s)
                assert r["alpha"] > 0 and r["beta"] > 0 and 0 < r["posterior_mean"] < 1
                assert r["posterior_mean"] == pytest.approx(float(ea / (ea + eb)), rel=1e-6)


# ---------------- (2) ancestor map caps ----------------
def amap(keys, per_key):
    return {f"k{i}": [f"t{j}" for j in range(per_key)] for i in range(keys)}


def test_ancestor_keys_cap_1000_accepted_1001_refused():
    assert b.phenotype_match_checked(["a"], ["b"], {f"k{i}": [] for i in range(1000)})["exact_matches"] == 0
    refuses(ValueError, "ancestor_map has more than 1000 keys", b.phenotype_match_checked, ["a"], ["b"], {f"k{i}": [] for i in range(1001)})


def test_ancestor_per_key_cap_100_accepted_101_refused_for_list_tuple_set():
    for kind in (list, tuple, set, frozenset):
        ok = {"a": kind(f"t{j}" for j in range(100))}
        assert b.phenotype_match_checked(["a"], ["t5"], ok)["semantic_partial"] == 0.5
        refuses(ValueError, "ancestor_map entry has more than 100 terms", b.phenotype_match_checked, ["a"], ["b"],
                {"a": kind(f"t{j}" for j in range(101))})


def test_ancestor_total_terms_cap_10000_accepted_10001_refused():
    assert b.phenotype_match_checked(["a"], ["b"], amap(100, 100))["exact_matches"] == 0              # 100 * 100 = 10000
    m = amap(100, 100); m["extra"] = ["x"]                                                           # 10001
    refuses(ValueError, "ancestor_map has more than 10000 terms in total", b.phenotype_match_checked, ["a"], ["b"], m)
    refuses(ValueError, "ancestor_map has more than 10000 terms in total", b.phenotype_match_checked, ["a"], ["b"], amap(101, 100))


def test_ancestor_budget_is_shared_across_candidates_in_reverse_inference():
    c = lambda: {"phenotypes": ["b"], "ancestor_map": amap(100, 50)}      # 5000 terms each
    assert len(b.reverse_inference_checked(["a"], [c(), c()])) == 2          # 10000 in total: accepted
    refuses(ValueError, "ancestor_map has more than 10000 terms in total", b.reverse_inference_checked, ["a"], [c(), c(), c()])


def test_ancestor_checks_happen_before_core_runs():
    calls = []
    orig = core.phenotype_match
    core.phenotype_match = lambda *a, **k: calls.append(1) or orig(*a, **k)
    try:
        with pytest.raises(ValueError):
            b.phenotype_match_checked(["a"], ["b"], amap(1, 101))
        with pytest.raises(ValueError):
            b.phenotype_match_checked([f"p{i}" for i in range(1000)], [f"d{i}" for i in range(101)])
    finally:
        core.phenotype_match = orig
    assert calls == []


# ---------------- (3) pair caps ----------------
def test_pair_cap_100000_accepted_and_next_step_refused():
    p = [f"p{i}" for i in range(1000)]
    t0 = time.time()
    r = b.phenotype_match_checked(p, [f"d{i}" for i in range(100)], amap(1, 100) | {"p0": ["d1"]})   # 1000 * 100 = 100000 pairs
    assert r["exact_matches"] == 0 and r["semantic_partial"] == 0.5
    assert time.time() - t0 < 5
    refuses(ValueError, "phenotype comparison has more than 100000 term pairs", b.phenotype_match_checked, p, [f"d{i}" for i in range(101)])


def test_pair_cap_exactly_at_cap_counts_equal_not_over():
    assert b.phenotype_match_checked(["a"] * 0 + [f"p{i}" for i in range(250)], [f"d{i}" for i in range(400)])["exact_matches"] == 0   # 250*400 = 100000
    refuses(ValueError, "phenotype comparison has more than 100000 term pairs", b.phenotype_match_checked,
            [f"p{i}" for i in range(251)], [f"d{i}" for i in range(400)])                                                              # 100400


def test_reverse_inference_pair_total_cap():
    p = [f"p{i}" for i in range(10)]
    cands = [{"phenotypes": [f"d{i}" for i in range(1000)]} for _ in range(10)]               # 10 * 10 * 1000 = 100000 pairs
    assert len(b.reverse_inference_checked(p, cands)) == 10
    refuses(ValueError, "candidates need more than 100000 phenotype term pairs in total", b.reverse_inference_checked, p,
            cands + [{"phenotypes": ["x"]}])                                                    # +10 pairs
    assert len(b.reverse_inference_checked(p, cands + [{"phenotypes": []}])) == 11              # zero-pair candidate adds nothing


def test_mean_rounding_to_one_with_positive_beta_is_refused():
    # a = 1e12, b = 1e-6 (> 0): 1e12 + 1e-6 rounds to 1e12 in floats, so the float mean is exactly 1 although beta > 0
    out = core.federated_evidence([], 1e12, 1e-6)
    assert out["beta"] > 0 and out["posterior_mean"] == 1
    refuses(ValueError, "posterior is not interior: beta or mean degenerate after float cancellation",
            b.federated_evidence_checked, [], 1e12, 1e-6)
    assert b.federated_evidence_checked([], 1e12, 1)["posterior_mean"] < 1
