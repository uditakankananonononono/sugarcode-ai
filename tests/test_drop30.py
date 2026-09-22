"""Drop 30: rarenet panel surfaces the U12 flags and exon-skip context from
deepsplice's live_splice_assessment - in the structured splice_assessment
dict AND in the readable score components."""
import pytest

import sugarcode.modules.rarenet_ai.core as rn


def _mocks(monkeypatch, sa):
    monkeypatch.setattr(rn, "enrich_variants_live",
                        lambda variants, offline=False: [
                            {"gene": "SCN1A", "hgvs": "c.383+1A>G",
                             "clinvar": {}, "gnomad": {}, "consequence": ""}])
    from sugarcode.bio import gnomad
    monkeypatch.setattr(gnomad, "gene_constraint",
                        lambda g, offline=False: {"lof_constrained": False})
    import sugarcode.modules.deepsplice as ds
    monkeypatch.setattr(ds, "live_splice_assessment", lambda g, n, offline=False: sa)


def test_panel_carries_u12_atac_flag(monkeypatch):
    _mocks(monkeypatch, {"status": "natural_site", "site_type": "donor",
                         "site_class": "AT", "delta": -0.158, "consequence": "loss",
                         "u12_atac": True, "u12_note": "AT-AC U12 note", "source": "fixture"})
    panel = rn.variant_evidence_panel([{"gene": "SCN1A", "hgvs": "c.383+1A>G"}], offline=True)
    row = panel["panel"][0]
    sa = row["splice_assessment"]
    assert sa["u12_atac"] is True and sa["u12_note"] == "AT-AC U12 note"
    assert sa["site_class"] == "AT"
    comp = next(c for c in row["score_components"] if "loss of natural donor" in c)
    assert "[AT-AC U12]" in comp and "+1.5" in comp


def test_panel_carries_u12_gtag_subtype_and_exon_context(monkeypatch):
    _mocks(monkeypatch, {"status": "natural_site", "site_type": "donor",
                         "delta": -0.152, "consequence": "loss",
                         "donor_subtype": "U12 GT-AG",
                         "exon_context": {"skipped_exon": {"length": 108},
                                          "in_frame": True,
                                          "conditional_prediction": "..."},
                         "source": "fixture"})
    panel = rn.variant_evidence_panel([{"gene": "SCN1A", "hgvs": "c.79+1T>A"}], offline=True)
    row = panel["panel"][0]
    sa = row["splice_assessment"]
    assert sa["donor_subtype"] == "U12 GT-AG"
    assert sa["exon_context"]["in_frame"] is True
    comp = next(c for c in row["score_components"] if "loss of natural donor" in c)
    assert "[U12 GT-AG]" in comp
    assert "108 nt in-frame" in comp


def test_panel_plain_u2_unchanged(monkeypatch):
    """A plain U2 GT-AG loss with no flags shows no U12/exon annotations."""
    _mocks(monkeypatch, {"status": "natural_site", "site_type": "donor",
                         "delta": -0.25, "consequence": "loss", "source": "fixture"})
    panel = rn.variant_evidence_panel([{"gene": "BRCA1", "hgvs": "c.212+1G>A"}], offline=True)
    row = panel["panel"][0]
    comp = next(c for c in row["score_components"] if "loss of natural donor" in c)
    assert "[" not in comp.split("(delta")[0] and "exon-skip" not in comp
