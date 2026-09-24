"""Primer toolkit: hand-computed NN thermodynamics, heuristics, picker,
Biopython oracle.

NN table vendored from Biopython 1.88 DNA_NN4 (SantaLucia 1998 unified
parameters + SantaLucia & Hicks 2004 terminal corrections) - PROVENANCE in
the module docstring. The oracle tests verify the implementation against
the reference implementation that vendors the same published values.
"""
import pytest

from sugarcode.bio.primer import (tm_nn, gc_percent, revcomp, max_homopolymer,
                                  hairpin_max_stem, self_dimer_max_run,
                                  pick_primers)


def test_tm_nn_hand_computed():
    # "AT" : init(0.2, -5.7) + init_oneG/C(0,0) [GC>0? no -> allA/T(0,0)]
    # ends A+T -> init_A/T x2: dh += 4.4, ds += 13.8
    # NN AT/TA: (-7.2, -20.4)
    # dh = 0.2 + 4.4 - 7.2 = -2.6 ; ds = -5.7 + 13.8 - 20.4 = -12.3
    # salt: ds += 0.368 * (2-1) * ln(0.05) = 0.368 * (-2.995732) = -1.102430
    # k = (25 - 12.5) nM = 1.25e-8 M
    # Tm = 1000 * -2.6 / (-13.40243 + 1.987 * ln(1.25e-8)) - 273.15
    import math
    ds = -12.3 + 0.368 * math.log(0.05)
    expect = 1000 * -2.6 / (ds + 1.987 * math.log(1.25e-8)) - 273.15
    assert tm_nn("AT") == pytest.approx(expect)


def test_tm_orderings_and_errors():
    assert tm_nn("GCGCGCGCGCGCGCGCGCGC") > tm_nn("AAAAAAAAAAAAAAAAAAAA")
    assert tm_nn("AAAAAAAAAAAAAAAAAAAA") > tm_nn("AAAAAAAAAA")
    with pytest.raises(ValueError, match="invalid bases"):
        tm_nn("ACGTN")
    with pytest.raises(ValueError, match="too short"):
        tm_nn("A")
    with pytest.raises(ValueError, match="positive"):
        tm_nn("ACGT", na_mm=0)
    with pytest.raises(ValueError, match="template_nm / 2"):
        tm_nn("ACGT", primer_nm=10, template_nm=40)


def test_basics():
    assert revcomp("AAACGT") == "ACGTTT"
    assert gc_percent("GGAT") == 50.0
    assert max_homopolymer("AAATTTTGG") == 4
    assert max_homopolymer("ATGCA") == 1


def test_hairpin_heuristic():
    assert hairpin_max_stem("GGGGAAACCCC") == 4      # perfect 4-stem, loop 3
    assert hairpin_max_stem("ATGCA") == 0
    # shorter stems with longer loops are legitimate folds
    assert hairpin_max_stem("GGGGAACCCC", min_loop=3) == 3
    # loop shorter than min_loop must not fold
    assert hairpin_max_stem("GGAACC", min_loop=3) == 0
    assert hairpin_max_stem("GGAACC", min_loop=2) == 2


def test_self_dimer_heuristic():
    d = self_dimer_max_run("GAATTC")                  # EcoRI: fully self-comp
    assert d == {"any": 6, "three_prime": 6}
    # disjoint alphabets between seq and its revcomp: no pairing possible
    assert self_dimer_max_run("AAAAGGGG")["any"] == 0
    # 3' complementarity: last 4 bases pair with another copy
    d2 = self_dimer_max_run("TTTTGCGC")
    assert d2["three_prime"] >= 3


def test_pick_primers_synthetic():
    import random
    random.seed(42)
    template = "".join(random.choice("ACGT") for _ in range(600))
    region = (250, 350)
    pairs = pick_primers(template, region, n=3)
    assert 1 <= len(pairs) <= 3
    for p in pairs:
        f, r = p["forward"], p["reverse"]
        assert template[f["start"]:f["end"]] == f["seq"]
        assert template[r["start"]:r["end"]] == revcomp(r["seq"])
        assert f["start"] <= region[0] and r["end"] >= region[1]
        assert p["product_size"] == r["end"] - f["start"] >= 100
        assert abs(f["tm"] - r["tm"]) <= 2.0
        assert 57.0 <= f["tm"] <= 63.0 and 57.0 <= r["tm"] <= 63.0
        assert 40.0 <= f["gc"] <= 60.0
        assert f["seq"][-1] in "GC" and r["seq"][-1] in "GC"
    assert [p["score"] for p in pairs] == sorted(p["score"]
                                                 for p in pairs)
    with pytest.raises(ValueError, match="region"):
        pick_primers(template, (350, 250))


# ------------------------- oracle: Biopython 1.88 -------------------------

oracle = pytest.importorskip("Bio", reason="Biopython oracle not installed")
from Bio.SeqUtils import MeltingTemp as mt  # noqa: E402

ORACLE_SEQS = ["CGTTCCAAAGATGTGGGCATGAGCTTAC", "AAAAAAAAAAAAAAAAAAAA",
               "GCGCGCGCGCGCGCGCGCGC", "TTTTGCGCA",
               "ATGCATGCATGCATGCATGC", "ACGTACGTACGTACGTACG",
               "GGGGCCCCAAAATTTT", "GAATTCGAATTC"]


@pytest.mark.parametrize("seq", ORACLE_SEQS)
def test_tm_against_biopython(seq):
    assert tm_nn(seq) == pytest.approx(
        mt.Tm_NN(seq, nn_table=mt.DNA_NN4, saltcorr=5), abs=1e-9)


def test_tm_oracle_salt_and_conc_variants():
    seq = ORACLE_SEQS[0]
    assert tm_nn(seq, na_mm=100) == pytest.approx(
        mt.Tm_NN(seq, nn_table=mt.DNA_NN4, Na=100), abs=1e-9)
    assert tm_nn(seq, primer_nm=500, template_nm=0) == pytest.approx(
        mt.Tm_NN(seq, nn_table=mt.DNA_NN4, dnac1=500, dnac2=0), abs=1e-9)
    assert tm_nn("GAATTCGAATTC", selfcomp=True) == pytest.approx(
        mt.Tm_NN("GAATTCGAATTC", nn_table=mt.DNA_NN4, selfcomp=True),
        abs=1e-9)
