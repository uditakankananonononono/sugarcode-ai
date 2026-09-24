"""Hermetic parity and behavior tests for the published CRISPRscan model."""
import hashlib
from importlib.resources import files

import pytest

from sugarcode.modules.crisprscan_score import score, score_many, scan_sequence

REFERENCE_CONTEXTS = [
    "CCCCCCCCCCCTGCTGATGCTAGATAAGGTTGTGA",
    "GGACCTATCGATGCTGATGCTAGATATGGTTGTGA",
    "GGAAAAAAAAAAACTGATGCTAGATACGGTTGTGA",
    "GGACCTATCGATGCTCGTGCTGGGTACGGTTGTGA",
    "GCCCCCCTCGATGCTGATGCTAGATAGGGCACACA",
]
REFERENCE_SCORES = [0.531, 0.531, 0.450, 0.712, 0.618]


def test_reference_implementation_parity():
    assert [round(score(s).score, 3) for s in REFERENCE_CONTEXTS] == REFERENCE_SCORES


def test_result_is_auditable_and_reconstructs_exactly():
    result = score(REFERENCE_CONTEXTS[3])
    assert result.spacer == result.context[6:26]
    assert result.pam == result.context[26:29]
    assert result.score == pytest.approx(result.intercept + result.feature_sum)
    assert result.feature_sum == pytest.approx(sum(x.coefficient for x in result.contributions))
    assert all(result.context[x.position_1_based - 1:][:len(x.motif)] == x.motif
               for x in result.contributions)
    assert "zebrafish" in result.applicability


def test_vendored_artifact_integrity():
    data = files("sugarcode.modules.crisprscan_score").joinpath("data/coefficients.csv").read_bytes()
    assert hashlib.sha256(data).hexdigest() == "6e3f1bbfd58e5426651a15cfd0db6ac2094e0a93158dc51639b5929fc9ced5a4"


@pytest.mark.parametrize("bad", [
    "A" * 34,
    "A" * 35,
    REFERENCE_CONTEXTS[0][:10] + "N" + REFERENCE_CONTEXTS[0][11:],
])
def test_strict_context_validation(bad):
    with pytest.raises(ValueError):
        score(bad)


def test_batch_missing_is_explicit_not_simulated():
    results = score_many([REFERENCE_CONTEXTS[0], "A" * 35], errors="missing")
    assert results[0] is not None
    assert results[1] is None
    with pytest.raises(ValueError):
        score_many(["A" * 35])


def test_scan_forward_coordinates_and_edge_omission():
    context = REFERENCE_CONTEXTS[2]
    seq = "TTTT" + context + "AAAA"
    hits = scan_sequence(seq)
    hit = next(h for h in hits if h["strand"] == "+" and h["context"] == context)
    assert (hit["start"], hit["end"]) == (10, 30)
    assert hit["spacer"] == context[6:26]
    assert hit["score"] == pytest.approx(score(context).score)


def test_scan_reverse_strand_coordinates():
    context = REFERENCE_CONTEXTS[4]
    rc = context.translate(str.maketrans("ACGT", "TGCA"))[::-1]
    seq = "AAAAA" + rc + "TTTTT"
    hit = next(h for h in scan_sequence(seq) if h["strand"] == "-" and h["context"] == context)
    assert (hit["start"], hit["end"]) == (14, 34)
    assert hit["spacer"] == context[6:26]


def test_scan_sorted_and_unambiguous_only():
    seq = REFERENCE_CONTEXTS[0] + "AAAAAA" + REFERENCE_CONTEXTS[3]
    hits = scan_sequence(seq)
    assert hits == sorted(hits, key=lambda h: (-h["score"], h["start"], h["strand"]))
    with pytest.raises(ValueError):
        scan_sequence(seq + "N")
