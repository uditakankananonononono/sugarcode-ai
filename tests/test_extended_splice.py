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
            "rb1": (124, 7), "scn1a": (97, 0)}


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
    assert (len(path), len(ben)) == (2050, 63)
    canon_u2 = [c for c in path if _k(c) <= 2 and _cls(c) in ("GT", "GC", "AG")]
    assert len(canon_u2) == 1802
    assert all(c["delta"] <= -0.15 for c in canon_u2)
    atac = [c for c in path if _k(c) <= 2 and _cls(c) in ("AT", "AC")]
    assert len(atac) == 8 and all(g == "scn1a" for c in atac
                                  for g in [next(g for g in ALL_GENES
                                                 if c in FIX[g]["pathogenic"])])
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
    assert not pwm_applicable("AAGATAAGT", "donor")
    assert not pwm_applicable("TAACAATAACCTACA", "acceptor")


def test_atac_variant_effect_not_interpretable():
    """Scoring an AT-AC site with the GT-AG PWM previously returned
    delta=0 'minimal effect' for real pathogenic +1 variants (SCN1A
    c.383+1A>G even scored +0.254 'strengthened'). Now flagged."""
    from sugarcode.modules.deepsplice import variant_at
    r = variant_at("TTCATATCC", 3, "G", "donor")   # SCN1A c.383+1A>G (AT-AC)
    assert r["site_class"] == "AT" and r["pwm_applicable"] is False
    assert "not applicable" in r["consequence"]
    r2 = variant_at("AAGGTAAGT", 3, "A", "donor")  # normal GT site unaffected
    assert r2["site_class"] == "GT" and r2["pwm_applicable"] is True


def test_atac_live_path_refuses_score(monkeypatch):
    """The product path must say 'atypical_site_class', never a score."""
    import sugarcode.bio.splice as sp
    from sugarcode.modules.deepsplice import live_splice_assessment
    monkeypatch.setattr(sp, "junction_map", lambda gene, offline=False: {
        "status": "ok", "donors": {383: "TTCATATCC"}, "acceptors": {},
        "sequence": "A" * 500, "strand": 1, "cds_spans": [(1, 250), (251, 383), (384, 500)],
        "source": "fixture"})
    r = live_splice_assessment("SCN1A", "c.383+1A>G")
    assert r["status"] == "atypical_site_class" and r["site_class"] == "AT"
    assert "delta" not in r
    # GT site on the same shape still scores
    monkeypatch.setattr(sp, "junction_map", lambda gene, offline=False: {
        "status": "ok", "donors": {383: "AAGGTAAGT"}, "acceptors": {},
        "sequence": "A" * 500, "strand": 1, "cds_spans": [(1, 250), (251, 383), (384, 500)],
        "source": "fixture"})
    r2 = live_splice_assessment("GENE", "c.383+1G>A")
    assert r2["status"] == "natural_site" and r2["delta"] <= -0.15


def test_scn1a_isoform_shift_documented():
    """SCN1A ClinVar cites NM_001165963 (extra 33-nt alt coding exon absent
    from NG_011906.1's NM_006920.4 annotation). Downstream coordinates were
    remapped -33, every surviving case ref-base verified: 42 -> 97 mapped,
    zero ref mismatches. The remaining unmapped cases (alt-exon-internal,
    deep k) stay dropped, not guessed."""
    src = FIX["scn1a"]["source"]
    assert "NM_006920" in src and "remapped" in src
    downstream = [c for c in FIX["scn1a"]["pathogenic"]
                  if int(re.search(r"c\.(\d+)", c["notation"]).group(1)) > 2589]
    assert len(downstream) >= 50  # the recovered isoform-shift cases
