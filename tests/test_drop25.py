"""Drop 25: splice evidence + ClinVar star tiers in the rarenet panel;
live_splice_assessment product path."""
import pytest

from sugarcode.modules.deepsplice import live_splice_assessment
from sugarcode.modules.rarenet_ai.core import variant_evidence_panel


def _patch_panel(monkeypatch, clinvar_hits, gnomad_freq, constraint):
    from sugarcode.bio import entrez, gnomad
    monkeypatch.setattr(entrez, "clinvar_exact", lambda g, n, offline=False: clinvar_hits)
    monkeypatch.setattr(gnomad, "variant_frequency",
                        lambda v, dataset="gnomad_r4", offline=False: gnomad_freq)
    monkeypatch.setattr(gnomad, "gene_constraint", lambda g, offline=False: constraint)


# --- live_splice_assessment (hermetic via cached records is NOT assumed:
#     these run offline=False only in live runs; unit behavior via monkeypatch)

def test_assessment_unparseable_and_no_map():
    r = live_splice_assessment("BRCA1", "p.Arg273His")
    assert r["status"] == "unparseable"
    r = live_splice_assessment("NO_SUCH_GENE", "c.1+1G>A")
    assert "no RefSeqGene junction map" in r["status"]


def test_assessment_natural_site(monkeypatch):
    import sugarcode.bio.splice as sp
    monkeypatch.setattr(sp, "junction_map", lambda gene, offline=False: {
        "status": "ok", "gene": gene, "accession": "NG_X",
        "donors": {212: "AAGGTAAGT"}, "acceptors": {},
        "sequence": "N" * 1000, "strand": 1, "cds_spans": [],
        "source": "fixture"})
    r = live_splice_assessment("GENE", "c.212+1G>A")
    assert r["status"] == "natural_site" and r["site_type"] == "donor"
    assert r["delta"] <= -0.15


def test_assessment_ref_mismatch_named(monkeypatch):
    import sugarcode.bio.splice as sp
    monkeypatch.setattr(sp, "junction_map", lambda gene, offline=False: {
        "status": "ok", "gene": gene, "accession": "NG_X",
        "donors": {212: "AAGGTAAGT"}, "acceptors": {},
        "sequence": "N" * 1000, "strand": 1, "cds_spans": [],
        "source": "fixture"})
    r = live_splice_assessment("GENE", "c.212+1A>G")   # window has G at +1
    assert r["status"] == "ref mismatch"


# --- panel: star tiers -------------------------------------------------------

def test_panel_star_tier_scaling(monkeypatch):
    _patch_panel(monkeypatch,
                 [{"uid": "1", "title": "NM_000546.6(TP53):c.818G>A (p.Arg273His)",
                   "significance": "Pathogenic",
                   "review_status": "criteria provided, single submitter", "condition": "LFS"}],
                 {"variant_id": "v", "present": False},
                 {"gene": "TP53", "lof_constrained": False})
    v = variant_evidence_panel([{"gene": "TP53", "hgvs": "p.Arg273His",
                                 "variant_id": "17-7674221-C-T", "consequence": "missense"}])["panel"][0]
    # 1-star: 2.0 * 0.3/0.8 = 0.75; +0.5 absent = 1.25
    assert v["support_score"] == 1.25
    assert any("1-star" in c for c in v["score_components"])


def test_panel_practice_guideline_outweighs_expert_panel(monkeypatch):
    _patch_panel(monkeypatch,
                 [{"uid": "1", "title": "NM_000546.6(TP53):c.215C>G (p.Pro72Arg)",
                   "significance": "Benign", "review_status": "practice guideline",
                   "condition": "x"}],
                 {"variant_id": "v", "present": True, "max_af": 0.716},
                 {"gene": "TP53", "lof_constrained": False})
    v = variant_evidence_panel([{"gene": "TP53", "hgvs": "p.Pro72Arg",
                                 "variant_id": "17-7676154-G-C"}])["panel"][0]
    # 4-star benign: -2.5; common AF -1.5 => -4.0
    assert v["support_score"] == -4.0


# --- panel: splice component -------------------------------------------------

def test_panel_splice_loss_component(monkeypatch):
    _patch_panel(monkeypatch, [], {"variant_id": "v", "present": False},
                 {"gene": "BRCA1", "lof_constrained": True, "loeuf": 0.3})
    import sugarcode.modules.deepsplice as ds
    monkeypatch.setattr(ds, "live_splice_assessment", lambda g, n, offline=False: {
        "gene": g, "notation": n, "status": "natural_site", "site_type": "donor",
        "delta": -0.25, "consequence": "likely loss of natural site",
        "source": "fixture"})
    v = variant_evidence_panel([{"gene": "BRCA1", "hgvs": "c.212+1G>A",
                                 "variant_id": "17-x-G-A",
                                 "consequence": "splice_donor"}])["panel"][0]
    # splice loss +1.5, absent +0.5, LOF constrained +0.5 = 2.5
    assert v["support_score"] == 2.5
    assert any("loss of natural donor site" in c for c in v["score_components"])
    assert v["splice_assessment"]["status"] == "natural_site"


def test_panel_cryptic_component(monkeypatch):
    _patch_panel(monkeypatch, [], {"variant_id": "v", "present": False},
                 {"gene": "CFTR", "lof_constrained": False})
    import sugarcode.modules.deepsplice as ds
    monkeypatch.setattr(ds, "live_splice_assessment", lambda g, n, offline=False: {
        "gene": g, "notation": n, "status": "cryptic_scan",
        "strong_findings": [{"type": "new_cryptic_site", "site_type": "donor",
                             "position": 56, "ref_score": 0.68, "alt_score": 0.92,
                             "sequence": "ATGGTGAGT"}],
        "verdict": "NEW cryptic donor", "source": "fixture"})
    v = variant_evidence_panel([{"gene": "CFTR", "hgvs": "c.3718-2477C>T",
                                 "variant_id": "7-x-C-T"}])["panel"][0]
    # cryptic +1.0, absent +0.5 = 1.5
    assert v["support_score"] == 1.5
    assert any("NEW cryptic donor" in c for c in v["score_components"])


def test_panel_weak_perturbation_scores_nothing(monkeypatch):
    _patch_panel(monkeypatch, [], {"variant_id": "v", "present": False},
                 {"gene": "BRCA1", "lof_constrained": False})
    import sugarcode.modules.deepsplice as ds
    monkeypatch.setattr(ds, "live_splice_assessment", lambda g, n, offline=False: {
        "gene": g, "notation": n, "status": "cryptic_scan", "strong_findings": [],
        "verdict": "weak only", "source": "fixture"})
    v = variant_evidence_panel([{"gene": "BRCA1", "hgvs": "c.5467+200G>A",
                                 "variant_id": "17-x-G-A"}])["panel"][0]
    # weak perturbation: 0; absent +0.5 = 0.5
    assert v["support_score"] == 0.5
    assert any("no strong cryptic" in c for c in v["score_components"])
