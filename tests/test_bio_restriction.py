"""Restriction digest toolkit: lambda known-answer digests, overhangs,
circular, Biopython oracle.

Lambda reference sequence: NC_001416.1 (48,502 bp, fetched from NCBI
2026-09-24, vendored in tests/data/lambda_NC_001416.fasta). NOTE: the
reference carries AAGCTC (not AAGCTT) at 37583-37588, so it yields 7
HindIII fragments; the classic 8-band commercial marker (6557 + 125)
appears when that variant base is patched - tested both ways.
"""
import random

import pytest

from sugarcode.bio.restriction import (digest, find_sites, enzyme_info,
                                       list_enzymes, gel_bands)
from sugarcode.bio.fasta import parse_fasta

LAMBDA = parse_fasta(open("tests/data/lambda_NC_001416.fasta").read())[0][
    "sequence"]


def test_lambda_hindiii_reference_and_marker_variant():
    assert len(LAMBDA) == 48502
    d = digest(LAMBDA, ["HindIII"])
    assert d["fragments"] == [23130, 9416, 6682, 4361, 2322, 2027, 564]
    assert d["n_sites"] == 6
    # commercial marker strain carries AAGCTT at 37583 -> classic 8 bands
    v = LAMBDA[:37588] + "T" + LAMBDA[37589:]
    assert v[37583:37589] == "AAGCTT"
    assert digest(v, ["HindIII"])["fragments"] == \
        [23130, 9416, 6557, 4361, 2322, 2027, 564, 125]


def test_enzyme_info_overhangs():
    e = enzyme_info("EcoRI")
    assert e["site"] == "GAATTC" and e["cut_top"] == 1
    assert e["cut_bottom"] == 5 and e["overhang"] == "5'"
    assert e["overhang_length"] == 4 and e["palindromic"]
    assert enzyme_info("PstI")["overhang"] == "3'"
    assert enzyme_info("SmaI")["overhang"] == "blunt"
    assert len(list_enzymes()) == 610
    with pytest.raises(ValueError, match="unknown enzyme"):
        enzyme_info("NotAnEnzyme")


def test_linear_digest_hand_computed():
    d = digest("TTTGAATTCAAA", ["EcoRI"])        # top cut at 3+1=4
    assert d["fragments"] == [8, 4]
    assert d["cuts"][0]["cut_top"] == 4 and d["cuts"][0]["strand"] == "+"
    # two enzymes, cuts merged
    d2 = digest("TTTGAATTCGGATCCAA", ["EcoRI", "BamHI"])
    assert d2["fragments"] == [7, 6, 4]     # bounds 0, 4, 10, 17


def test_circular_digest():
    assert digest("TTTGAATTCAAA", ["EcoRI"], circular=True)["fragments"] == [12]
    assert digest("AAAAAA", ["EcoRI"], circular=True)["fragments"] == [6]
    # site spanning the origin is found in circular mode
    seq = "AATTCAAAAG"
    assert find_sites(seq, "EcoRI") == []                 # linear: split site
    hits = find_sites(seq, "EcoRI", circular=True)        # G at end + AATTC
    assert len(hits) == 1 and hits[0]["start"] == 9


def test_non_palindromic_both_strands():
    # padded upstream: on the - strand BsmBI cuts 1-5 nt 5' of GAGACG, which must lie inside a linear molecule
    hits = find_sites("AAAAAAAAGAGACGAAAAAA", "BsmBI")    # revcomp(CGTCTC)
    assert len(hits) == 1 and hits[0]["strand"] == "-"
    assert enzyme_info("BsmBI")["palindromic"] is False


def test_gel_bands_monotonic():
    bands = gel_bands([10000, 1000, 100])
    migs = [b["rel_migration"] for b in bands]
    assert migs == sorted(migs)                            # larger = slower
    assert gel_bands([100])[0]["rel_migration"] == pytest.approx(0.9)
    assert gel_bands([10000])[0]["rel_migration"] == pytest.approx(0.1)


# ------------------------- oracle: Biopython 1.88 -------------------------

oracle = pytest.importorskip("Bio", reason="Biopython oracle not installed")
from Bio.Restriction import EcoRI, BamHI, HindIII, PstI, KpnI, NotI, BsmBI  # noqa: E402
from Bio.Seq import Seq  # noqa: E402

PAIRS = [("EcoRI", EcoRI), ("BamHI", BamHI), ("HindIII", HindIII),
         ("PstI", PstI), ("KpnI", KpnI), ("NotI", NotI), ("BsmBI", BsmBI)]


def test_oracle_linear_random_sequences():
    random.seed(7)
    for _ in range(10):
        seq = "".join(random.choice("ACGT") for _ in range(3000))
        for name, bio_e in PAIRS:
            mine = digest(seq, [name])["fragments"]
            sites = bio_e.search(Seq(seq))
            # Biopython cut positions are 1-based coordinates of the first
            # base AFTER the cut: consistent bounds are 1..len+1
            bounds = [1] + sites + [len(seq) + 1]
            theirs = sorted([b - a for a, b in zip(bounds, bounds[1:])],
                            reverse=True)
            assert mine == theirs


def test_oracle_circular_random_sequences():
    random.seed(11)
    for _ in range(5):
        seq = "".join(random.choice("ACGT") for _ in range(3000))
        for name, bio_e in [("EcoRI", EcoRI), ("HindIII", HindIII)]:
            mine = digest(seq, [name], circular=True)["fragments"]
            sites = bio_e.search(Seq(seq), linear=False)
            if not sites:
                theirs = [len(seq)]
            else:
                frags = ([b - a for a, b in zip(sites, sites[1:])]
                         + [sites[0] + len(seq) - sites[-1]])
                theirs = sorted(frags, reverse=True)
            assert mine == theirs
