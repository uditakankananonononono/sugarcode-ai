"""Drop 36: alternative_outcomes (intron retention, cryptic-use candidates)
reach the rarenet and openclinvar readable outputs. The structured data has
flowed since drop 34 inside exon_context; this drop surfaces it in the
component/evidence strings."""
import pytest

import sugarcode.modules.openclinvar.core as oc
import sugarcode.modules.rarenet_ai.core as rn

SA = {"status": "natural_site", "site_type": "donor", "delta": -0.254,
      "consequence": "loss", "source": "fixture",
      "exon_context": {"skipped_exon": {"cdna_start": 1, "cdna_end": 212,
                                        "length": 78},
                       "in_frame": True,
                       "conditional_prediction": "...",
                       "alternative_outcomes": {
                           "intron_retention": ("intron retention (1499 nt, not a "
                                                "multiple of 3): frameshift -> PTC/NMD"),
                           "cryptic_use": {"candidates": [
                               {"offset_nt": -22, "score": 0.861,
                                "sequence": "TATGTAAGA"}]}}}}


def _mocks(monkeypatch):
    from sugarcode.bio import gnomad, entrez
    monkeypatch.setattr(gnomad, "gene_constraint",
                        lambda g, offline=False: {"lof_constrained": False})
    monkeypatch.setattr(entrez, "clinvar_exact", lambda g, v, offline=False: [])
    import sugarcode.modules.deepsplice as ds
    monkeypatch.setattr(ds, "live_splice_assessment", lambda g, n, offline=False: SA)
    monkeypatch.setattr(rn, "enrich_variants_live",
                        lambda variants, offline=False: [
                            {"gene": "BRCA1", "hgvs": "c.212+1G>A",
                             "clinvar": {}, "gnomad": {}, "consequence": ""}])


def test_openclinvar_detail_shows_outcomes(monkeypatch):
    _mocks(monkeypatch)
    r = oc.interpret_variant_live("BRCA1", "c.212+1G>A")
    ev = next(e for e in r["evidence"] if e["rule"] == "SPLICE_PWM_LOSS")
    assert "intron retention (1499 nt" in ev["detail"]
    assert "cryptic donor candidate at -22 nt (0.86)" in ev["detail"]


def test_rarenet_component_shows_outcomes(monkeypatch):
    _mocks(monkeypatch)
    panel = rn.variant_evidence_panel([{"gene": "BRCA1", "hgvs": "c.212+1G>A"}], offline=True)
    row = panel["panel"][0]
    comp = next(c for c in row["score_components"] if "loss of natural donor" in c)
    assert "intron retention (1499 nt" in comp
    assert "cryptic donor candidate at -22 nt (0.86)" in comp
    # structured payload still flows inside exon_context
    assert row["splice_assessment"]["exon_context"]["alternative_outcomes"]
