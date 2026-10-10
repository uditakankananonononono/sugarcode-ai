"""REUSE LABEL: bytes copied from the reviewed, discarded commit fe074b1840e2d59d08373d11473a51136f17db04
(same test file, other path); the only change is removal of the `is` identity assertion and a test rename.
No new history is claimed for the reused bytes.
P03 characterization of bio.genbank.revcomp and bio.genbank.transcript_exons (current behavior).

AUTHORED BY READING ONLY, NOT RUN. Source re-read at cb004816 (fresh chronology 21:18:30-21:18:48): bio/genbank.py 1-103 in full.
Findings only: no other-module IUPAC comparison, no standard or defect claim, no fix.
genbank.revcomp is the LOCAL function (RC = str.maketrans("ACGTN", "TGCAN")), not primer/restriction revcomp.
"""
from sugarcode.bio.genbank import parse_location, revcomp, transcript_exons


def test_revcomp_acgt_and_acgtn_adjacent_controls():
    assert revcomp("ACGT") == "ACGT"
    assert revcomp("AACGT") == "ACGTT"
    assert revcomp("ACGTN") == "NACGT"


def test_revcomp_iupac_letters_pass_through_and_are_only_reversed():
    assert revcomp("RYKM") == "MKYR"


def test_revcomp_lowercase_passes_through_and_is_only_reversed():
    assert revcomp("acgt") == "tgca"


def test_revcomp_empty_string():
    assert revcomp("") == ""


def test_transcript_exons_plus_strand_keeps_span_order():
    feat = {"spans": [(1, 9), (20, 28)], "strand": 1}
    got = transcript_exons(feat)
    assert got == [(1, 9), (20, 28)]


def test_transcript_exons_minus_strand_reverses_span_order_and_input_value_is_unchanged():
    feat = {"spans": [(1, 9), (20, 28)], "strand": -1}
    assert transcript_exons(feat) == [(20, 28), (1, 9)]
    assert feat["spans"] == [(1, 9), (20, 28)]


def test_composition_outer_complement_multispan_location_then_transcript_exons():
    # composition finding: parse_location output fed to transcript_exons (parser result is not new)
    spans, strand = parse_location("complement(join(1..9,20..28))")
    assert (spans, strand) == ([(1, 9), (20, 28)], -1)
    assert transcript_exons({"spans": spans, "strand": strand}) == [(20, 28), (1, 9)]
