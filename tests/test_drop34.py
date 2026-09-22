"""Drop 34: exon_context deepened with alternative outcomes of natural-site
loss - intron retention (real intron length from RefSeqGene CDS spans,
frame call, PTC/NMD honesty, long-intron caveat) and cryptic-site use
(strongest pre-existing same-type sites in the +/-60 nt flank, transcript
orientation, natural site excluded, dinucleotide-viable only: GT/GC donor,
AG acceptor). Two off-by-ones caught and fixed during live verify: the
acceptor window is -14..+1 (last base is the first EXONIC base), so its
junction boundary is pos+wlen-1; and score-only candidates included
dinucleotide-dead sites (AAGGAAAAG "donor") until filtered. UTR losses
carry no alternative_outcomes (no genomic spans in the UTR map - named,
not guessed)."""
import pytest

from sugarcode.modules.deepsplice import live_splice_assessment


def test_donor_loss_outcomes_brca1():
    sa = live_splice_assessment("BRCA1", "c.212+1G>A")
    alt = sa["exon_context"]["alternative_outcomes"]
    assert "1499 nt" in alt["intron_retention"]
    assert "not a multiple of 3" in alt["intron_retention"]
    assert "rarely observed for long introns" in alt["intron_retention"]
    cands = alt["cryptic_use"]["candidates"]
    assert cands and all(c["sequence"][3:5] in ("GT", "GC") for c in cands)
    top = cands[0]
    # the documented exon-5 cryptic donor 22 nt upstream, near-natural score
    assert top["offset_nt"] == -22 and top["score"] >= 0.8
    assert "truncation" in alt["cryptic_use"]["note"]


def test_acceptor_loss_outcomes_brca1():
    sa = live_splice_assessment("BRCA1", "c.135-1G>T")
    alt = sa["exon_context"]["alternative_outcomes"]
    assert "9192 nt" in alt["intron_retention"] and "in-frame" in alt["intron_retention"]
    cands = alt["cryptic_use"]["candidates"]
    assert cands and all(c["sequence"][12:14] == "AG" for c in cands)
    # natural site excluded: no candidate may sit at offset 0
    assert all(c["offset_nt"] != 0 for c in cands)


def test_minus_strand_outcomes_f8():
    sa = live_splice_assessment("F8", "c.670+1G>A")
    alt = sa["exon_context"]["alternative_outcomes"]
    assert "2433 nt" in alt["intron_retention"]
    assert all(c["sequence"][3:5] in ("GT", "GC")
               for c in alt["cryptic_use"]["candidates"])


def test_utr_loss_has_no_alternative_outcomes():
    sa = live_splice_assessment("GJB2", "c.-23+1G>A")
    assert sa["exon_context"].get("alternative_outcomes") is None
    assert sa["exon_context"]["utr"] is True  # skipping context still there
