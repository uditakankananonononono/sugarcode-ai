"""Drop 38: UTR routing on explicit-transcript maps (the named drop-33 gap).
bio.splice.cdna_full_junction_map aligns the transcript's WHOLE cDNA record
to the RefSeqGene genomic sequence, so 5'-UTR introns get negative c. keys
on ClinVar's own transcript. Honest catches fixed on live verify: (1) the
CDS-start check wrongly required the segment to START near the CDS start
(GJB2's CDS starts mid-exon-2 - the requirement is that the start base is
covered); (2) the acceptor window was sliced one base left (fully intronic)
- the convention is 14 intronic + the first EXONIC base; (3) the minus-strand
branch double-revcomped - the cDNA aligns to target=rc(genome) in its own
orientation, so target slices are already transcript-oriented. Minus-strand
branch note: all RefSeqGene records probed are gene-oriented (strand +1), so
the minus branch is reviewed but not live-exercised - named honestly."""
import pytest

from sugarcode.bio.splice import cdna_full_junction_map, cdna_junction_map
from sugarcode.modules.deepsplice import live_splice_assessment


def test_gjb2_full_map_utr_keys():
    jm = cdna_full_junction_map("GJB2", "NM_004004.6")
    assert jm["status"] == "ok" and jm["coverage"] == 1.0
    assert jm["donors"] == {-23: "CAGGTGAGC"}
    assert jm["acceptors"] == {-22: "TTCGTCTTTTCCAGA"}  # 14 intronic + first exonic


def test_scn1a_full_map_parity_and_leader_note():
    f = cdna_full_junction_map("SCN1A", "NM_001165963.2")
    c = cdna_junction_map("SCN1A", "NM_001165963.2")
    shared = set(f["donors"]) & set(c["donors"])
    assert len(shared) == 25
    assert all(f["donors"][k] == c["donors"][k] for k in shared)
    assert "5'-UTR bases absent" in f["source"]  # curated leader, skipped not guessed


def test_utr_assessment_on_explicit_transcript():
    sa = live_splice_assessment("GJB2", "c.-23+1G>A", transcript="NM_004004.6")
    assert sa["status"] == "natural_site" and sa["delta"] <= -0.15
    assert sa["exon_context"]["utr"] is True
    assert "NM_004004.6 full-cDNA" in sa["source"]
    sa2 = live_splice_assessment("GJB2", "c.-22-2A>C", transcript="NM_004004.6")
    assert sa2["status"] == "natural_site" and sa2["delta"] <= -0.15
