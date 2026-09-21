"""Drop 19: rarenet combined evidence panel."""
import pytest


class TestEvidencePanel:
    def _patch(self, monkeypatch, clinvar_hits, gnomad_freq, constraint):
        from sugarcode.bio import entrez, gnomad
        monkeypatch.setattr(entrez, "clinvar_exact", lambda g, n, offline=False: clinvar_hits)
        monkeypatch.setattr(gnomad, "variant_frequency", lambda v, dataset="gnomad_r4", offline=False: gnomad_freq)
        monkeypatch.setattr(gnomad, "gene_constraint", lambda g, offline=False: constraint)

    def test_pathogenic_plus_absent_is_strong(self, monkeypatch):
        self._patch(monkeypatch,
                    [{"uid": "1", "title": "NM_000546.6(TP53):c.818G>A (p.Arg273His)",
                      "significance": "Pathogenic", "review_status": "reviewed by expert panel", "condition": "LFS"}],
                    {"variant_id": "v", "present": False},
                    {"gene": "TP53", "lof_constrained": False})
        from sugarcode.modules.rarenet_ai.core import variant_evidence_panel
        r = variant_evidence_panel([{"gene": "TP53", "hgvs": "p.Arg273His",
                                     "variant_id": "17-7674221-C-T", "consequence": "missense"}])
        v = r["panel"][0]
        assert v["support_score"] == 2.5 and v["evidence_class"] == "strong support"
        assert "Not a diagnosis" in r["disclaimer"]

    def test_benign_plus_common_is_against(self, monkeypatch):
        self._patch(monkeypatch,
                    [{"uid": "1", "title": "NM_000546.6(TP53):c.215C>G (p.Pro72Arg)",
                      "significance": "Benign", "review_status": "reviewed by expert panel", "condition": "x"}],
                    {"variant_id": "v", "present": True, "max_af": 0.716},
                    {"gene": "TP53", "lof_constrained": False})
        from sugarcode.modules.rarenet_ai.core import variant_evidence_panel
        v = variant_evidence_panel([{"gene": "TP53", "hgvs": "p.Pro72Arg",
                                     "variant_id": "17-7676154-G-C"}])["panel"][0]
        assert v["support_score"] == -3.5 and v["evidence_class"] == "evidence against"

    def test_lof_constrained_component(self, monkeypatch):
        self._patch(monkeypatch, [], {"variant_id": "v", "present": False},
                    {"gene": "SCN1A", "lof_constrained": True, "loeuf": 0.107})
        from sugarcode.modules.rarenet_ai.core import variant_evidence_panel
        v = variant_evidence_panel([{"gene": "SCN1A", "hgvs": "c.100dup",
                                     "variant_id": "2-1-A-AT",
                                     "consequence": "frameshift"}])["panel"][0]
        # absent from gnomAD (+0.5) + LOF in constrained gene (+0.5) = 1.0
        assert v["support_score"] == 1.0 and v["evidence_class"] == "moderate support"

    def test_ranking_orders_by_score(self, monkeypatch):
        self._patch(monkeypatch, [], {"variant_id": "v", "present": False},
                    {"gene": "X", "lof_constrained": True, "loeuf": 0.1})
        from sugarcode.modules.rarenet_ai.core import variant_evidence_panel
        r = variant_evidence_panel([{"gene": "X", "hgvs": "c.1A>G", "consequence": "missense"},
                                    {"gene": "X", "hgvs": "c.2dup", "consequence": "frameshift"}])
        scores = [v["support_score"] for v in r["panel"]]
        assert scores == sorted(scores, reverse=True)

    def test_exact_query_used_when_notation_present(self, monkeypatch):
        from sugarcode.bio import entrez, gnomad
        calls = []
        monkeypatch.setattr(entrez, "clinvar_exact", lambda g, n, offline=False: calls.append(n) or [])
        monkeypatch.setattr(gnomad, "variant_frequency", lambda v, dataset="gnomad_r4", offline=False: {"present": False})
        monkeypatch.setattr(gnomad, "gene_constraint", lambda g, offline=False: {"gene": g, "lof_constrained": False})
        from sugarcode.modules.rarenet_ai.core import enrich_variants_live
        enrich_variants_live([{"gene": "TP53", "hgvs": "p.Arg273His"}])
        assert calls == ["p.Arg273His"]
