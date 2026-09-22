"""Drop 37: AT-AC calibration report. Separates circular from independent
evidence: 7 of 9 golden windows overlap the 139-intron training set (the
SCN-family intron is in intronIC - their ref scores are circular), but
SCN1A's SECOND AT-AC intron windows (donor AAGATAAGT at c.4476, acceptor
TTTCTTTTCTATACT at c.4477) are NOT in training - fully independent windows,
and their pathogenic variants are still called loss. All 16 variant deltas
are independent ClinVar evidence and all are loss (-0.158 donor / -0.205
acceptor). Position-level: the four pathogenic columns carry +1.98 for the
conserved base vs -6.14 for any substitution."""
import json
from pathlib import Path

CAL = json.loads(Path("src/sugarcode/bio/data/splice_sites/atac_calibration.json").read_text())


def test_all_16_deltas_loss():
    assert len(CAL["variant_deltas"]) == 16
    assert all(d["delta"] <= -0.15 for d in CAL["variant_deltas"])
    assert {d["delta"] for d in CAL["variant_deltas"]} == {-0.158, -0.205}


def test_circularity_is_named_per_window():
    wins = {w["window"]: w for w in CAL["circularity"]["windows"]}
    assert len(wins) == 9
    # SCN1A's second AT-AC intron: independent of training
    assert wins["AAGATAAGT"]["in_training"] is False
    assert wins["TTTCTTTTCTATACT"]["in_training"] is False
    # the conserved family intron windows: circular (named, not hidden)
    assert wins["TTCATATCC"]["in_training"] is True
    independent = [w for w in wins.values() if not w["in_training"]]
    assert len(independent) == 2


def test_pathogenic_position_logodds_decisive():
    po = CAL["position_logodds"]
    for key, conserved in (("acceptor_-2(A)", "A"), ("acceptor_-1(C)", "C"),
                           ("donor_+1(A)", "A"), ("donor_+2(T)", "T")):
        col = po[key]
        assert col[conserved] > 1.5
        assert all(v < -5 for b, v in col.items() if b != conserved)
