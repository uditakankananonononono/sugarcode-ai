"""Drop 33: UTR routing. live_splice_assessment now parses negative c.
numbers and routes them through bio.splice.utr_junction_map - mRNA-exon
junctions with c.1 anchored at the paired CDS start (exonic walk, NOT
genomic distance: the first implementation keyed GJB2's donor at -3202 by
counting the intron; caught and fixed). GJB2 end-to-end: c.-23+1G>A donor
loss with UTR-correct exon_context (no frame language on untranslated
exons). Both panels (openclinvar, rarenet) accept UTR notations."""
import pytest

from sugarcode.bio.splice import junction_map, utr_junction_map
from sugarcode.modules.deepsplice import live_splice_assessment


def test_gjb2_utr_map_offline():
    jm = utr_junction_map("GJB2")
    assert jm["status"] == "ok" and jm["transcript"].startswith("NM_004004")
    assert jm["donors"] == {-23: "CAGGTGAGC"}
    assert jm["acceptors"] == {-22: "TTCGTCTTTTCCAGA"}
    assert jm["exons"][0]["cdna_end"] == -23 and jm["exons"][1]["cdna_start"] == -22


def test_brca1_utr_map_extends_cds_map_consistently():
    cds = junction_map("BRCA1")
    utr = utr_junction_map("BRCA1")
    shared = set(cds["donors"]) & set(utr["donors"])
    assert shared and all(cds["donors"][k] == utr["donors"][k] for k in shared)
    assert -20 in utr["donors"] and -20 not in cds["donors"]  # real 5'-UTR intron


def test_gjb2_utr_variants_assessed_end_to_end():
    sa = live_splice_assessment("GJB2", "c.-23+1G>A")
    assert sa["status"] == "natural_site" and sa["site_type"] == "donor"
    assert sa["delta"] <= -0.15
    esc = sa["exon_context"]
    assert esc["utr"] is True and esc["in_frame"] is None
    assert "5'-UTR exon" in esc["conditional_prediction"]
    sa2 = live_splice_assessment("GJB2", "c.-22-2A>C")
    assert sa2["status"] == "natural_site" and sa2["delta"] <= -0.15
    # a made-up ref allele is still caught, not scored
    assert live_splice_assessment("GJB2", "c.-23+3C>T")["status"] == "ref mismatch"


def test_positive_numbering_unchanged():
    sa = live_splice_assessment("BRCA1", "c.212+1G>A")
    assert sa["status"] == "natural_site" and sa["delta"] <= -0.15
    assert sa["exon_context"]["in_frame"] is True  # coding exon keeps frame language


def test_panels_route_utr_notations(monkeypatch):
    """openclinvar + rarenet must pass UTR notations to the assessment."""
    import sugarcode.modules.openclinvar.core as oc
    import sugarcode.modules.rarenet_ai.core as rn
    import sugarcode.modules.deepsplice as ds
    from sugarcode.bio import gnomad, entrez
    monkeypatch.setattr(gnomad, "gene_constraint",
                        lambda g, offline=False: {"lof_constrained": False})
    monkeypatch.setattr(entrez, "clinvar_exact", lambda g, v, offline=False: [])
    monkeypatch.setattr(ds, "live_splice_assessment", lambda g, n, offline=False: {
        "status": "natural_site", "site_type": "donor", "delta": -0.254,
        "consequence": "loss", "source": "fixture"})
    r = oc.interpret_variant_live("GJB2", "c.-23+1G>A")
    assert any(e["rule"] == "SPLICE_PWM_LOSS" for e in r["evidence"])
    monkeypatch.setattr(rn, "enrich_variants_live",
                        lambda variants, offline=False: [
                            {"gene": "GJB2", "hgvs": "c.-23+1G>A",
                             "clinvar": {}, "gnomad": {}, "consequence": ""}])
    panel = rn.variant_evidence_panel([{"gene": "GJB2", "hgvs": "c.-23+1G>A"}])
    row = panel["panel"][0]
    assert row["splice_assessment"]["status"] == "natural_site"
    assert any("loss of natural donor" in c for c in row["score_components"])
