"""Drop 32: GJB2 5'-UTR intron golden. GJB2 was the one harvested gene
excluded in drop 29 (single-exon CDS); its real splice biology is a 5'-UTR
intron. All three pathogenic ClinVar UTR-intron variants are called loss
on the real NM_004004.6 windows: c.-23+1G>A donor (-0.254), c.-22-1G>A and
expert-panel c.-22-2A>C acceptors (-0.184). Honest scope: scoring-level
golden via variant_at; live_splice_assessment does not yet route negative
(UTR) c. numbers - documented follow-on. No benign cases fit the window
(c.-23+12G>A benign sits at +12; c.-22-2A>G is conflicting, excluded)."""
import json
from pathlib import Path

FIX = json.loads(Path("tests/fixtures/gjb2_utr_golden.json").read_text())


def test_fixture_shape():
    assert len(FIX["cases"]) == 3
    assert "NM_004004" in FIX["source"]
    assert all(c["sig"] == "pathogenic" for c in FIX["cases"])


def test_all_utr_variants_called_loss():
    by_notation = {c["notation"]: c for c in FIX["cases"]}
    assert by_notation["c.-23+1G>A"]["site_type"] == "donor"
    assert by_notation["c.-23+1G>A"]["delta"] <= -0.15
    assert by_notation["c.-22-1G>A"]["site_type"] == "acceptor"
    assert by_notation["c.-22-1G>A"]["delta"] <= -0.15
    ep = by_notation["c.-22-2A>C"]
    assert ep["delta"] <= -0.15 and "expert panel" in ep["review"]


def test_utr_windows_are_real_gt_ag():
    donor = next(c for c in FIX["cases"] if c["site_type"] == "donor")
    acc = next(c for c in FIX["cases"] if c["site_type"] == "acceptor")
    assert donor["window"] == "CAGGTGAGC" and donor["window"][3:5] == "GT"
    assert acc["window"] == "TTCGTCTTTTCCAGA" and acc["window"][12:14] == "AG"
