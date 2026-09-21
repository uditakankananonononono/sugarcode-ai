"""Hermetic parity and invariant tests for the published MIT/Hsu model."""
import hashlib
from importlib.resources import files
import pytest
from sugarcode.modules.mit_offtarget import aggregate_specificity, score, score_many

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


def test_upstream_reference_parity():
    assert [round(score(GUIDE, s, p).score, 3) for s, p in SITES] == [1, .259, .069, .016, 1, .104, .003]


def test_penalties_reconstruct_score_and_positions_are_one_based():
    r = score(GUIDE, SITES[-1][0], "NGG")
    assert r.mismatch_positions == (1, 10, 13, 20)
    assert r.score == pytest.approx(r.position_penalty_product * r.count_penalty * r.distance_penalty * r.pam_penalty)
    assert r.mean_mismatch_distance == pytest.approx(19 / 3)


def test_distance_toggle_matches_reference_formula():
    target = SITES[-1][0]
    with_distance = score(GUIDE, target, "AGG")
    without = score(GUIDE, target, "AGG", include_distance=False)
    assert without.distance_penalty == 1
    assert without.score > with_distance.score


def test_aggregate_specificity_excludes_on_target_and_is_bounded():
    r = aggregate_specificity(GUIDE, SITES)
    assert r.excluded_on_targets == 1
    assert r.scored_sites == 6
    assert r.specificity == pytest.approx(100 / (1 + r.off_target_sum))
    assert 0 < r.specificity <= 100


def test_duplicate_risky_sites_reduce_specificity():
    one = aggregate_specificity(GUIDE, [SITES[-1]], exclude_exact_on_target=False)
    two = aggregate_specificity(GUIDE, [SITES[-1], SITES[-1]], exclude_exact_on_target=False)
    assert two.specificity < one.specificity


@pytest.mark.parametrize("guide,off,pam", [
    ("A" * 19, "A" * 20, "AGG"),
    ("A" * 20, "A" * 19, "AGG"),
    ("A" * 19 + "N", "A" * 20, "AGG"),
    ("A" * 20, "A" * 20, "ANN"),
])
def test_strict_validation(guide, off, pam):
    with pytest.raises(ValueError):
        score(guide, off, pam)


def test_batch_missing_is_explicit():
    r = score_many(GUIDE, [SITES[0], ("N" * 20, "AGG")], errors="missing")
    assert r[0] is not None and r[1] is None


def test_vendored_artifact_hashes():
    data = files("sugarcode.modules.mit_offtarget").joinpath("data")
    assert hashlib.sha256(data.joinpath("position_weights.tsv").read_bytes()).hexdigest() == "467d6e821a03b2b2b6caa97bc913b2c35302640e37ec93c85375b3a2ebf80dcb"
    assert hashlib.sha256(data.joinpath("pam_weights.tsv").read_bytes()).hexdigest() == "3f83c4f659cda48795312c080f8528984a3ce25f9b2475d79cb80b4835fb3b45"
