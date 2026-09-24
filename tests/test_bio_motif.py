"""Motif toolkit: hand-computed PWM/log-odds, two-strand scanning, JASPAR."""
import math

import pytest

from sugarcode.bio.motif import (from_alignment, from_iupac, iupac_consensus,
                                 score_site, threshold_score, scan, best_hit,
                                 read_jaspar, write_jaspar)

JASPAR = """>MA0001.1 TEST
A  [ 8 0 1 ]
C  [ 1 9 1 ]
G  [ 0 1 8 ]
T  [ 1 0 0 ]
"""


def test_pwm_from_alignment_hand_computed():
    m = from_alignment(["ACGT", "ACGT"])
    # counts: target base 2.5, others 0.5, total 4
    assert m["pwm"][0]["A"] == pytest.approx(0.625)
    assert m["pwm"][0]["C"] == pytest.approx(0.125)
    assert m["lod"][0]["A"] == pytest.approx(math.log2(2.5))
    assert m["lod"][0]["C"] == pytest.approx(-1.0)
    assert m["min_score"] == pytest.approx(-4.0)
    assert m["max_score"] == pytest.approx(4 * math.log2(2.5))
    assert score_site("ACGT", m) == pytest.approx(4 * math.log2(2.5))
    assert score_site("AAAA", m) == pytest.approx(math.log2(2.5) - 3.0)
    with pytest.raises(ValueError, match="equal length"):
        from_alignment(["ACG", "ACGT"])


def test_from_iupac_uniform_positions():
    m = from_iupac("RY")
    assert m["pwm"][0] == {"A": 0.5, "G": 0.5, "C": 0.0, "T": 0.0}
    assert m["pwm"][1]["C"] == 0.5
    assert iupac_consensus(m) == "RY"
    with pytest.raises(ValueError, match="IUPAC"):
        from_iupac("AX")
    with pytest.raises(ValueError, match="empty"):
        from_iupac("")


def test_threshold_and_scan_both_strands():
    m = from_alignment(["ACGT", "ACGT"])
    th = threshold_score(m, 0.5)
    assert th == pytest.approx((m["min_score"] + m["max_score"]) / 2)
    with pytest.raises(ValueError, match="\\[0, 1\\]"):
        threshold_score(m, 1.1)
    # perfect site on the minus strand: revcomp(ACGT)=ACGT embedded rev
    seq = "TTTTACGTTTTT"
    hits = scan(seq, m, threshold_fraction=0.99)
    assert {h["strand"] for h in hits} == {"+", "-"}
    assert all(h["start"] == 4 and h["end"] == 8 for h in hits)
    assert hits[0]["score"] == pytest.approx(4 * math.log2(2.5), abs=1e-4)
    fwd = scan(seq, m, threshold_fraction=0.99, both_strands=False)
    assert {h["strand"] for h in fwd} == {"+"}
    assert scan("AC", m, threshold_fraction=0.5) == []   # too short
    with pytest.raises(ValueError, match="not both"):
        scan(seq, m, threshold=0.0, threshold_fraction=0.8)


def test_best_hit_hand_computed():
    mot = read_jaspar(JASPAR, pseudocount=0.0)[0]
    h = best_hit("GGGACGGG", mot, both_strands=False)
    expect = math.log2(3.2) + math.log2(3.6) + math.log2(3.2)
    assert h["start"] == 3 and h["matched"] == "ACG"
    assert h["score"] == pytest.approx(round(expect, 4))
    with pytest.raises(ValueError, match="shorter"):
        best_hit("AC", mot)


def test_jaspar_roundtrip_and_validation():
    mot = read_jaspar(JASPAR, pseudocount=0.0)[0]
    assert mot["name"] == "MA0001.1 TEST" and mot["length"] == 3
    assert mot["pwm"][1]["C"] == pytest.approx(0.9)
    mot2 = read_jaspar(write_jaspar([mot]))[0]
    assert mot2["length"] == 3
    # multi-matrix file
    two = read_jaspar(JASPAR + JASPAR.replace("MA0001.1", "MA0002.1"))
    assert [m["name"].split()[0] for m in two] == ["MA0001.1", "MA0002.1"]
    with pytest.raises(ValueError, match="before any header"):
        read_jaspar("A [ 1 2 ]\n")
    with pytest.raises(ValueError, match="exactly 4 rows"):
        read_jaspar(">X\nA [ 1 ]\nC [ 1 ]\nG [ 1 ]\n")
    with pytest.raises(ValueError, match="different lengths"):
        read_jaspar(">X\nA [ 1 2 ]\nC [ 1 ]\nG [ 1 ]\nT [ 1 ]\n")
