"""Hermetic exact-parity tests for the published Doench 2016 CFD model."""
import hashlib
from importlib.resources import files
import pytest
from sugarcode.modules.cfd_offtarget import score, score_many, summarize_risk

GUIDE = "ATCGATGCTGATGCTAGATA"
SITES = [
    ("ATCGATGCTGATGCTAGATA", "AGG"),
    ("ATCGATGCTGATGCTAGATA", "AAG"),
    ("ATCGATGCTGATGCTAGATA", "AGA"),
    ("ATCGATGCTGATGCTAGATA", "AGT"),
    ("TTCGATGCTGATGCTAGATA", "AGG"),
    ("TTCGATGCTGATGCTAGATG", "AGG"),
    ("TTCGATGCTAATCCTAGATG", "AGG"),
]


def test_all_upstream_reference_fixtures():
    assert [round(score(GUIDE, s, p).score, 3) for s, p in SITES] == [1, .259, .069, .016, 1, .765, .301]


def test_mismatch_audit_reconstructs_exact_score():
    r = score(GUIDE, SITES[-1][0], "NGG")
    assert tuple(x.position_1_based for x in r.mismatches) == (1, 10, 13, 20)
    assert r.mismatch_count == 4
    assert r.mismatch_product == pytest.approx(__import__("math").prod(x.weight for x in r.mismatches))
    assert r.score == pytest.approx(r.mismatch_product * r.pam_weight)


def test_all_pam_cores_are_defined_and_noncanonical_are_penalized():
    scores = {a+b: score(GUIDE, GUIDE, a+b).score for a in "ACGT" for b in "ACGT"}
    assert len(scores) == 16
    assert scores["GG"] == 1
    assert scores["AG"] == pytest.approx(.259259259)
    assert scores["AA"] == 0


def test_summary_excludes_exact_target_and_tracks_high_risk():
    r = summarize_risk(GUIDE, SITES)
    assert r.excluded_on_targets == 1 and r.scored_sites == 6
    assert r.high_risk_sites == 4
    assert r.normalized_specificity == pytest.approx(100 / (1 + r.total_cfd_activity))


def test_summary_completeness_is_caller_controlled():
    one = summarize_risk(GUIDE, [SITES[-1]], exclude_exact_on_target=False)
    two = summarize_risk(GUIDE, [SITES[-1], SITES[-1]], exclude_exact_on_target=False)
    assert two.total_cfd_activity == pytest.approx(2 * one.total_cfd_activity)
    assert two.normalized_specificity < one.normalized_specificity


def test_batch_missing_is_explicit_not_simulated():
    r = score_many(GUIDE, [SITES[0], ("N" * 20, "AGG")], errors="missing")
    assert r[0] is not None and r[1] is None


@pytest.mark.parametrize("guide,off,pam", [
    ("A" * 19, "A" * 20, "AGG"), ("A" * 20, "A" * 19, "AGG"),
    ("A" * 19 + "N", "A" * 20, "AGG"), ("A" * 20, "A" * 20, "ANN"),
])
def test_strict_validation(guide, off, pam):
    with pytest.raises(ValueError): score(guide, off, pam)


def test_vendored_artifact_integrity():
    data = files("sugarcode.modules.cfd_offtarget").joinpath("data")
    assert hashlib.sha256(data.joinpath("mismatch_weights.tsv").read_bytes()).hexdigest() == "636e1d8e65f429db8c578036a673cb4516e896c05f594e3ab134734aab84dafc"
    assert hashlib.sha256(data.joinpath("pam_weights.tsv").read_bytes()).hexdigest() == "3f83c4f659cda48795312c080f8528984a3ce25f9b2475d79cb80b4835fb3b45"
