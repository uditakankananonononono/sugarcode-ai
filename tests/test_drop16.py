"""Drop 16: ClinVar priors in neohunter, mutdock vina baseline, gnomAD in rarenet."""
import pytest


class TestNeoHunterClinVar:
    def _fx_rec(self):
        seq = "M" + "E" * 271 + "R" + "A" * 120
        return {"accession": "P04637", "sequence": seq, "length": len(seq), "features": []}

    def test_clinvar_prior_attached_with_caveat(self, monkeypatch):
        from sugarcode.bio import uniprot, entrez
        monkeypatch.setattr(uniprot, "search", lambda g, organism_id=9600, offline=False: self._fx_rec())
        fx = [{"uid": "1", "title": "NM_000546.6(TP53):c.818G>A (p.Arg273His)",
               "significance": "Pathogenic", "review_status": "reviewed by expert panel",
               "condition": "Li-Fraumeni syndrome"}]
        monkeypatch.setattr(entrez, "clinvar_exact", lambda g, n, offline=False: fx)
        from sugarcode.modules.neohunter import find_neoantigens_live
        r = find_neoantigens_live("TP53", 273, "H")
        cp = r["clinvar_prior"]
        assert cp["significance"] == "Pathogenic"
        assert "not tumor-specific" in cp["tumor_specificity_caveat"]

    def test_clinvar_miss_leaves_none(self, monkeypatch):
        from sugarcode.bio import uniprot, entrez
        monkeypatch.setattr(uniprot, "search", lambda g, organism_id=9600, offline=False: self._fx_rec())
        monkeypatch.setattr(entrez, "clinvar_exact", lambda g, n, offline=False: [])
        from sugarcode.modules.neohunter import find_neoantigens_live
        assert find_neoantigens_live("TP53", 273, "H")["clinvar_prior"] is None

    def test_clinvar_failure_reported(self, monkeypatch):
        from sugarcode.bio import uniprot, entrez
        monkeypatch.setattr(uniprot, "search", lambda g, organism_id=9600, offline=False: self._fx_rec())
        def boom(g, n, offline=False): raise entrez.EntrezError("offline")
        monkeypatch.setattr(entrez, "clinvar_exact", boom)
        from sugarcode.modules.neohunter import find_neoantigens_live
        assert "lookup failed" in find_neoantigens_live("TP53", 273, "H")["clinvar_prior"]["status"]


class TestMutDockVinaBaseline:
    def test_vina_baseline_per_drug(self, monkeypatch):
        from sugarcode.modules.mutdock import core as md
        import sugarcode.modules.docking_studio.vina as vina
        monkeypatch.setattr(md, "resistance_scan", lambda seq, drugs, pocket_start=1: {"scan": True})
        monkeypatch.setattr(vina, "dock_vina_grid",
                            lambda atoms, smi: {"vina_score": -1.0, "estimated_dg_kcal_mol": -1.0})
        # avoid structure fetch: patch the fetchers used inside structure_resistance_scan
        import sugarcode.bio.structures as st
        fx = {"source": "fixture", "residues": [
            {"resnum": i, "resname": "ALA", "chain": "A", "ca": (i * 3.0, 0.0, 0.0), "bfactor": 10.0}
            for i in range(1, 15)]}
        monkeypatch.setattr(st, "fetch_pdb", lambda i, offline=False: fx)
        import sugarcode.modules.alpha_fold_ui.core as af
        monkeypatch.setattr(af, "_real_pockets", lambda res: [{"residues": list(range(1, 8))}])
        r = md.structure_resistance_scan("1FIX", {"drug": "CC"}, chain="A")
        assert r["wt_vina_baseline"]["drug"]["vina_score"] == -1.0
        assert "NOT re-docked" in r["wt_vina_note"]


class TestGnomAD:
    def test_present_variant_interpreted(self, monkeypatch):
        from sugarcode.bio import gnomad
        monkeypatch.setattr(gnomad, "variant_frequency",
                            lambda vid, dataset="gnomad_r4", offline=False:
                            {"variant_id": vid, "present": True, "max_af": 0.71})
        from sugarcode.modules.rarenet_ai.core import enrich_variants_live
        r = enrich_variants_live([{"gene": "TP53", "variant_id": "17-7676154-G-C"}])[0]
        assert "too common" in r["gnomad"]["rarity_interpretation"]

    def test_absent_is_real_answer(self, monkeypatch):
        from sugarcode.bio import gnomad
        monkeypatch.setattr(gnomad, "variant_frequency",
                            lambda vid, dataset="gnomad_r4", offline=False:
                            {"variant_id": vid, "present": False,
                             "note": "no carriers observed in gnomAD"})
        from sugarcode.modules.rarenet_ai.core import enrich_variants_live
        r = enrich_variants_live([{"gene": "TP53", "variant_id": "17-7674221-C-T"}])[0]
        assert r["gnomad"]["present"] is False

    def test_failure_reported_and_no_id_skipped(self, monkeypatch):
        from sugarcode.bio import gnomad
        def boom(vid, dataset="gnomad_r4", offline=False): raise gnomad.GnomADError("offline")
        monkeypatch.setattr(gnomad, "variant_frequency", boom)
        from sugarcode.modules.rarenet_ai.core import enrich_variants_live
        r = enrich_variants_live([{"gene": "TP53", "variant_id": "17-1-A-T"},
                                  {"gene": "BRCA1"}])
        assert "lookup failed" in r[0]["gnomad"]["status"]
        assert "skipped" in r[1]["gnomad"]["status"]

    def test_connector_error_propagation(self, monkeypatch):
        from sugarcode.bio import gnomad
        monkeypatch.setattr(gnomad, "_post", lambda q, offline=False: {"errors": [{"message": "x"}]})
        with pytest.raises(gnomad.GnomADError):
            gnomad.variant_frequency("17-1-A-T")
