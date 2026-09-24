"""Pairwise alignment: hand-computed fixtures, traceback invariant,
Biopython PairwiseAligner oracle.

Gap convention (Biopython-compatible): length-L gap costs
gap_open + (L-1) x gap_extend. BLOSUM62 vendored from Biopython
(Henikoff & Henikoff 1992; data/alignment/PROVENANCE.md).
"""
import random

import pytest

from sugarcode.bio.align import nw_align, sw_align, load_blosum62


def test_global_hand_computed():
    r = nw_align("AA", "AA")
    assert r["score"] == 4 and r["aligned_a"] == "AA"
    assert r["identity"] == 1.0
    # 1 match + 1-gap (open only): 2 - 5 = -3
    assert nw_align("AC", "A")["score"] == -3
    # 1 match + 2-gap (open + 1 extend): 2 - 5 - 1 = -4
    assert nw_align("ACC", "A")["score"] == -4
    # mismatch is better than two 1-gaps here: -1 > 2 x -5
    r = nw_align("AG", "TA")
    assert r["score"] == -2 and r["gap_positions"] == 0


def test_local_hand_computed():
    r = sw_align("TTACGT", "GGACGGA")
    assert r["score"] == 6 and r["aligned_a"] == "ACG"
    assert r["aligned_b"] == "ACG"
    # no positive region: empty local alignment scores 0
    r = sw_align("AAAA", "TTTT", mismatch=-3)
    assert r["score"] == 0 and r["aligned_a"] == ""


def test_blosum62_mode():
    bm = load_blosum62()
    assert bm["W"]["W"] == 11 and bm["K"]["K"] == 5 and bm["W"]["A"] == -3
    assert nw_align("WWK", "WWK", matrix="BLOSUM62")["score"] == 27
    assert nw_align("W", "A", matrix="BLOSUM62")["score"] == -3
    with pytest.raises(ValueError, match="unknown matrix"):
        nw_align("AA", "AA", matrix="PAM250")
    with pytest.raises(ValueError, match="not in the substitution"):
        nw_align("WWJ", "WWK", matrix="BLOSUM62")


def test_validation():
    with pytest.raises(ValueError, match="non-empty"):
        nw_align("", "A")
    with pytest.raises(ValueError, match="invalid DNA letters"):
        nw_align("ACGTU", "A")


def _rescore(r, match, mismatch, go, ge, matrix):
    aa, bb = r["aligned_a"], r["aligned_b"]
    total, i = 0, 0
    while i < len(aa):
        if aa[i] == "-" or bb[i] == "-":
            j = i
            while (j < len(aa) and (aa[j] == "-" or bb[j] == "-")
                   and (aa[j] == "-") == (aa[i] == "-")):
                j += 1
            total += go + (j - i - 1) * ge
            i = j
        else:
            total += (matrix[aa[i]][bb[i]] if matrix
                      else (match if aa[i] == bb[i] else mismatch))
            i += 1
    return total


def test_traceback_rescore_invariant():
    bm = load_blosum62()
    random.seed(9)
    for fn in (nw_align, sw_align):
        for _ in range(20):
            a = "".join(random.choice("ACGT")
                        for _ in range(random.randint(5, 30)))
            b = "".join(random.choice("ACGT")
                        for _ in range(random.randint(5, 30)))
            r = fn(a, b)
            assert len(r["aligned_a"]) == len(r["aligned_b"])
            assert _rescore(r, 2, -1, -5, -1, None) == \
                pytest.approx(r["score"])
        for _ in range(10):
            a = "".join(random.choice("ARNDCQEGHILKMFPSTWYV")
                        for _ in range(random.randint(5, 40)))
            b = "".join(random.choice("ARNDCQEGHILKMFPSTWYV")
                        for _ in range(random.randint(5, 40)))
            r = fn(a, b, gap_open=-11, gap_extend=-2, matrix="BLOSUM62")
            assert _rescore(r, 0, 0, -11, -2, bm) == \
                pytest.approx(r["score"])


# ------------------------- oracle: Biopython 1.88 -------------------------

oracle = pytest.importorskip("Bio", reason="Biopython oracle not installed")
from Bio.Align import PairwiseAligner, substitution_matrices  # noqa: E402


def test_oracle_dna_scores():
    al = PairwiseAligner()
    random.seed(3)
    for mode, fn in [("global", nw_align), ("local", sw_align)]:
        al.mode = mode
        al.match_score, al.mismatch_score = 2, -1
        al.open_gap_score, al.extend_gap_score = -5, -1
        for _ in range(15):
            a = "".join(random.choice("ACGT")
                        for _ in range(random.randint(5, 30)))
            b = "".join(random.choice("ACGT")
                        for _ in range(random.randint(5, 30)))
            assert fn(a, b)["score"] == pytest.approx(al.score(a, b))


def test_oracle_blosum62_scores():
    bm = substitution_matrices.load("BLOSUM62")
    al = PairwiseAligner()
    al.substitution_matrix = bm
    al.open_gap_score, al.extend_gap_score = -11, -2
    random.seed(4)
    for mode, fn in [("global", nw_align), ("local", sw_align)]:
        al.mode = mode
        for _ in range(10):
            a = "".join(random.choice("ARNDCQEGHILKMFPSTWYV")
                        for _ in range(random.randint(5, 40)))
            b = "".join(random.choice("ARNDCQEGHILKMFPSTWYV")
                        for _ in range(random.randint(5, 40)))
            mine = fn(a, b, gap_open=-11, gap_extend=-2,
                      matrix="BLOSUM62")["score"]
            assert mine == pytest.approx(al.score(a, b))
