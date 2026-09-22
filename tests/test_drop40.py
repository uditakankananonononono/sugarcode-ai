"""Drop 40: 3'-UTR intron support (c.*N numbering).

TP53's RefSeqGene record (NG_017013.2) carries a fully 3'-UTR intron on the
map's CDS-paired mRNA NM_001126118.1: donor c.*35, acceptor c.*36.
Live-verified windows 2026-09-22: donor CAGGTGAGT, acceptor TCTGTCTCCTACAGC.
Caveat (live-verified): NM_000546.5 - the transcript ClinVar cites for TP53 -
has NO 3'-UTR intron; the intron is isoform-specific, so c.*N keys follow the
mRNA named in the map's source string and must be checked per transcript.
"""
import sys
sys.path.insert(0, "src")
import pytest
from sugarcode.bio.splice import utr_junction_map
from sugarcode.modules.deepsplice import live_splice_assessment


def test_tp53_3utr_junction_map():
    jm = utr_junction_map("TP53")
    star_d = {k: v for k, v in jm["donors"].items() if isinstance(k, str)}
    star_a = {k: v for k, v in jm["acceptors"].items() if isinstance(k, str)}
    assert star_d == {"*35": "CAGGTGAGT"}
    assert star_a == {"*36": "TCTGTCTCCTACAGC"}
    # 3'-UTR exons numbered c.*N, never None
    assert all(e["cdna_start"] is not None and e["cdna_end"] is not None
               for e in jm["exons"])


def test_gjb2_5utr_map_unchanged():
    jm = utr_junction_map("GJB2")
    assert jm["donors"] == {-23: "CAGGTGAGC"}
    assert jm["acceptors"] == {-22: "TTCGTCTTTTCCAGA"}


def test_kcnq1_fails_loud():
    # KCNQ1's record carries a CDS feature with no spans: honest status, no crash
    jm = utr_junction_map("KCNQ1")
    assert jm["status"] == "no CDS spans in record"


def test_assess_3utr_donor():
    sa = live_splice_assessment("TP53", "c.*35+1G>A")
    assert sa["status"] == "natural_site" and sa["site_type"] == "donor"
    assert sa["delta"] < -0.15
    esc = sa["exon_context"]
    assert esc["utr"] is True and esc["in_frame"] is None
    assert "3'-UTR" in esc["conditional_prediction"]


def test_assess_3utr_acceptor():
    sa = live_splice_assessment("TP53", "c.*36-1G>A")
    assert sa["status"] == "natural_site" and sa["site_type"] == "acceptor"
    assert sa["delta"] < -0.15


def test_assess_3utr_ref_mismatch_fails_loud():
    sa = live_splice_assessment("TP53", "c.*35+3A>T")
    assert sa["status"] == "ref mismatch"


def test_assess_3utr_with_transcript_out_of_scope():
    sa = live_splice_assessment("TP53", "c.*35+1G>A", transcript="NM_000546.6")
    assert sa["status"] == "outside scope"


def test_panel_regexes_accept_3utr():
    import re
    assert re.fullmatch(r"c\.(?:-?\d+|\*\d+)[+-]\d+[ACGT]>[ACGT]", "c.*35+1G>A")
    assert re.fullmatch(r"c\.(?:-?\d+|\*\d+)[+-]\d+[ACGT]>[ACGT]", "c.135-1G>A")
    assert re.fullmatch(r"c\.(?:-?\d+|\*\d+)[+-]\d+[ACGT]>[ACGT]", "c.-23+1G>A")
    assert not re.fullmatch(r"c\.(?:-?\d+|\*\d+)[+-]\d+[ACGT]>[ACGT]", "c.*35del")


def test_explicit_transcript_selection():
    # NM_000546.5 (ClinVar's cited TP53 transcript) has no 3'-UTR intron;
    # the isoform NM_001126118.1 does - selection must follow the transcript.
    jm = utr_junction_map("TP53", transcript="NM_000546")
    assert not any(isinstance(k, str) for k in jm["donors"])
    assert "NM_000546.5" in jm["source"]
    jm2 = utr_junction_map("TP53", transcript="NM_001126118")
    assert set(k for k in jm2["donors"] if isinstance(k, str)) == {"*35"}
    assert utr_junction_map("TP53", transcript="NM_999999")["status"] == \
        "transcript NM_999999 not on record"
