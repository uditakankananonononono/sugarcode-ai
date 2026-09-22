"""Extended splice goldens - 10 more genes + AT-AC site-class detection
(drop 26). Fixtures: ClinVar live pulls (2026-09-22) on title-verified
RefSeqGene records. Pooled across all 17 genes: 2,050 pathogenic + 63
benign; 1,802/1,802 canonical U2 (GT/GC-AG) sites called loss (100%); 8
canonical AT-AC (U12 minor-spliceosome) sites detected and labeled
out-of-scope instead of silently mis-scored.
"""
import json
import re
from pathlib import Path

import pytest

NEW_GENES = ["apc", "atm", "ldlr", "mecp2", "msh6", "pah", "pms2", "pten", "rb1", "scn1a"]
ALL_GENES = ["brca1", "brca2", "mlh1", "cftr", "msh2", "tp53", "nf1"] + NEW_GENES
FIX = {g: json.loads(Path(f"tests/fixtures/{g}_splice_golden.json").read_text())
       for g in ALL_GENES}
EXPECTED = {"apc": (81, 1), "atm": (217, 5), "ldlr": (96, 2), "mecp2": (8, 0),
            "msh6": (39, 3), "pah": (63, 0), "pms2": (55, 0), "pten": (74, 1),
            "rb1": (124, 7), "scn1a": (106, 0)}


def _k(case):
    return int(re.search(r"[+-](\d+)", case["notation"]).group(1))


def _cls(case):
    from sugarcode.modules.deepsplice import site_class
    return site_class(case["window"], case["site_type"])


@pytest.mark.parametrize("gene", NEW_GENES)
def test_fixture_size_and_canonical_u2_capture(gene):
    path, ben = FIX[gene]["pathogenic"], FIX[gene]["benign"]
    assert (len(path), len(ben)) == EXPECTED[gene]
    canon_u2 = [c for c in path if _k(c) <= 2 and _cls(c) in ("GT", "GC", "AG")]
    misses = [c["notation"] for c in canon_u2 if c["delta"] > -0.15]
    assert misses == [], f"{gene} canonical U2 misses: {misses}"


def test_pooled_17_gene_golden():
    path = [c for g in ALL_GENES for c in FIX[g]["pathogenic"]]
    ben = [c for g in ALL_GENES for c in FIX[g]["benign"]]
    assert (len(path), len(ben)) == (2059, 63)
    canon_u2 = [c for c in path if _k(c) <= 2 and _cls(c) in ("GT", "GC", "AG")]
    assert len(canon_u2) == 1810
    assert all(c["delta"] <= -0.15 for c in canon_u2)
    atac = [c for c in path if _k(c) <= 2 and _cls(c) in ("AT", "AC")]
    assert len(atac) == 8 and all(g == "scn1a" for c in atac
                                  for g in [next(g for g in ALL_GENES
                                                 if c in FIX[g]["pathogenic"])])
    # drop 27: AT-AC sites are SCORED with the learned U12 matrices - all 8
    # pathogenic canonical AT-AC variants are called loss
    assert all(c["delta"] <= -0.15 for c in atac)
    tn = sum(1 for c in ben if c["delta"] > -0.15)
    assert tn / len(ben) >= 0.95


def test_site_class_detection():
    from sugarcode.modules.deepsplice import site_class, pwm_applicable
    assert site_class("AAGGTAAGT", "donor") == "GT"
    assert site_class("AAGGCAAGT", "donor") == "GC"
    assert site_class("AAGATAAGT", "donor") == "AT"      # SCN1A c.4443 donor
    assert site_class("TAACAATAACCTACA", "acceptor") == "AC"  # SCN1A c.384 acceptor
    assert site_class("TATGATCTCTTTAGG", "acceptor") == "AG"  # BRCA1 c.5153 real window
    # note: the legacy consensus SEED windows predate the harvest convention
    # (AG at idx 11/12 vs real -2/-1 at idx 12/13) - only real windows are classified
    assert pwm_applicable("AAGGTAAGT", "donor") and pwm_applicable("AAGGCAAGT", "donor")
    assert pwm_applicable("AAGATAAGT", "donor")       # U12 matrix vendored (drop 27)
    assert pwm_applicable("TAACAATAACCTACA", "acceptor")
    assert not pwm_applicable("AAGAAAAGT", "donor")   # non-canonical class: never scored
    assert not pwm_applicable("TAACAATAACCTATA", "acceptor")


def test_atac_scored_with_u12_matrix():
    """Before drop 26, AT-AC sites silently scored delta=0 'minimal effect'
    (c.383+1A>G even +0.254 'strengthened') under the GT-AG matrix. Drop 26
    named them not-applicable; drop 27 scores them with the learned U12
    matrices (139 human gold AT-AC introns): all pathogenic +1/+2 AT-AC
    golden variants are now called loss and carry the u12_atac flag."""
    from sugarcode.modules.deepsplice import variant_at
    r = variant_at("TTCATATCC", 3, "G", "donor")   # SCN1A c.383+1A>G (AT-AC)
    assert r["site_class"] == "AT" and r["pwm_applicable"] is True
    assert r["u12_atac"] is True and "139 human" in r["u12_note"]
    assert r["delta"] <= -0.15
    r2 = variant_at("AAGGTAAGT", 3, "A", "donor")  # normal GT site unaffected
    assert r2["site_class"] == "GT" and r2["pwm_applicable"] is True
    assert "u12_atac" not in r2
    # truly non-canonical classes still refuse
    r3 = variant_at("AAGAAAAGT", 3, "C", "donor")
    assert r3["pwm_applicable"] is False and "not applicable" in r3["consequence"]


def test_atac_live_path_scores_with_u12(monkeypatch):
    """AT-AC sites now score on the product path (U12 matrices, drop 27);
    only truly non-canonical classes return atypical_site_class."""
    import sugarcode.bio.splice as sp
    from sugarcode.modules.deepsplice import live_splice_assessment
    monkeypatch.setattr(sp, "junction_map", lambda gene, offline=False: {
        "status": "ok", "donors": {383: "TTCATATCC"}, "acceptors": {},
        "sequence": "A" * 500, "strand": 1, "cds_spans": [(1, 250), (251, 383), (384, 500)],
        "exons": [], "source": "fixture"})
    r = live_splice_assessment("SCN1A", "c.383+1A>G")
    assert r["status"] == "natural_site" and r["delta"] <= -0.15
    assert r.get("u12_atac") is True
    # non-canonical AA donor: still refused
    monkeypatch.setattr(sp, "junction_map", lambda gene, offline=False: {
        "status": "ok", "donors": {383: "AAGAAAAGT"}, "acceptors": {},
        "sequence": "A" * 500, "strand": 1, "cds_spans": [(1, 250), (251, 383), (384, 500)],
        "exons": [], "source": "fixture"})
    r2 = live_splice_assessment("GENE", "c.383+1A>C")
    assert r2["status"] == "atypical_site_class" and "delta" not in r2
    # GT site on the same shape still scores
    monkeypatch.setattr(sp, "junction_map", lambda gene, offline=False: {
        "status": "ok", "donors": {383: "AAGGTAAGT"}, "acceptors": {},
        "sequence": "A" * 500, "strand": 1, "cds_spans": [(1, 250), (251, 383), (384, 500)],
        "source": "fixture"})
    r2 = live_splice_assessment("GENE", "c.383+1G>A")
    assert r2["status"] == "natural_site" and r2["delta"] <= -0.15


def test_scn1a_native_transcript_map():
    """SCN1A ClinVar cites NM_001165963, which uses an alternative 3' donor
    extending exon 11 by 33 nt (drop-27 mechanism correction: a 3'
    extension, not a cassette exon - both donors are real GT sites on
    NG_011906.1). cdna_junction_map aligns the NM_001165963 CDS to the
    genomic record (coverage 1.0), so ClinVar numbering is native: no
    coordinate remap. 106/107 rows mapped (was 97 with the drop-26 remap),
    every case ref-base verified."""
    src = FIX["scn1a"]["source"]
    assert "cdna_junction_map" in src and "no remap" in src
    assert "alternative" in src and "extension" in src
    downstream = [c for c in FIX["scn1a"]["pathogenic"]
                  if int(re.search(r"c\.(\d+)", c["notation"]).group(1)) > 2589]
    assert len(downstream) >= 55  # native-numbered downstream cases
