"""Drop 18: gnomAD constraint in openclinvar, frequency in neohunter, binding-site validation."""
import pytest


class TestConstraintInOpenClinvar:
    def test_constrained_gene_supports_lof(self, monkeypatch):
        from sugarcode.bio import gnomad, entrez
        monkeypatch.setattr(gnomad, "gene_constraint", lambda g, offline=False:
                            {"gene": g, "pli": 1.0, "loeuf": 0.107, "lof_constrained": True})
        monkeypatch.setattr(entrez, "clinvar_exact", lambda g, v, offline=False: [])
        from sugarcode.modules.openclinvar import interpret_variant_live
        r = interpret_variant_live("SCN1A", "c.100dup", consequence="frameshift")
        ev = [e for e in r["evidence"] if e["rule"] == "GNOMAD_CONSTRAINT"][0]
        assert ev["weight"] > 0

    def test_unconstrained_gene_adds_no_support(self, monkeypatch):
        from sugarcode.bio import gnomad, entrez
        monkeypatch.setattr(gnomad, "gene_constraint", lambda g, offline=False:
                            {"gene": g, "pli": 0.0, "loeuf": 0.93, "lof_constrained": False})
        monkeypatch.setattr(entrez, "clinvar_exact", lambda g, v, offline=False: [])
        from sugarcode.modules.openclinvar import interpret_variant_live
        r = interpret_variant_live("BRCA1", "c.100dup", consequence="frameshift")
        ev = [e for e in r["evidence"] if e["rule"] == "GNOMAD_CONSTRAINT"][0]
        assert ev["weight"] == 0.0 and "no" in ev["detail"]

    def test_missense_no_constraint_evidence(self, monkeypatch):
        from sugarcode.bio import gnomad, entrez
        monkeypatch.setattr(gnomad, "gene_constraint", lambda g, offline=False:
                            {"gene": g, "pli": 1.0, "loeuf": 0.1, "lof_constrained": True})
        monkeypatch.setattr(entrez, "clinvar_exact", lambda g, v, offline=False: [])
        from sugarcode.modules.openclinvar import interpret_variant_live
        r = interpret_variant_live("SCN1A", "c.100A>G", consequence="missense")
        assert not any(e["rule"] == "GNOMAD_CONSTRAINT" for e in r["evidence"])
        assert r["gnomad_constraint"]["loeuf"] == 0.1

    def test_failure_reported(self, monkeypatch):
        from sugarcode.bio import gnomad, entrez
        def boom(g, offline=False): raise gnomad.GnomADError("offline")
        monkeypatch.setattr(gnomad, "gene_constraint", boom)
        monkeypatch.setattr(entrez, "clinvar_exact", lambda g, v, offline=False: [])
        from sugarcode.modules.openclinvar import interpret_variant_live
        assert "lookup failed" in interpret_variant_live("BRCA1", "c.100A>G", consequence="missense")["gnomad_constraint"]["status"]


class TestNeoHunterGnomAD:
    def _fx_rec(self):
        seq = "M" + "E" * 271 + "R" + "A" * 120
        return {"accession": "P04637", "sequence": seq, "length": len(seq), "features": []}

    def test_frequency_attached_when_id_given(self, monkeypatch):
        from sugarcode.bio import uniprot, entrez, gnomad
        monkeypatch.setattr(uniprot, "search", lambda g, organism_id=9600, offline=False: self._fx_rec())
        monkeypatch.setattr(entrez, "clinvar_exact", lambda g, n, offline=False: [])
        monkeypatch.setattr(gnomad, "variant_frequency", lambda v, dataset="gnomad_r4", offline=False:
                            {"variant_id": v, "present": False})
        from sugarcode.modules.neohunter import find_neoantigens_live
        r = find_neoantigens_live("TP53", 273, "H", variant_id="17-7674221-C-T")
        assert "tumor-specific" in r["gnomad_frequency"]["specificity_note"]

    def test_skipped_without_id(self, monkeypatch):
        from sugarcode.bio import uniprot, entrez
        monkeypatch.setattr(uniprot, "search", lambda g, organism_id=9600, offline=False: self._fx_rec())
        monkeypatch.setattr(entrez, "clinvar_exact", lambda g, n, offline=False: [])
        from sugarcode.modules.neohunter import find_neoantigens_live
        assert "skipped" in find_neoantigens_live("TP53", 273, "H")["gnomad_frequency"]["status"]


class TestBindingSiteValidation:
    def _setup(self, monkeypatch, features):
        from sugarcode.modules.mutdock import core as md
        import sugarcode.bio.structures as st
        import sugarcode.modules.alpha_fold_ui.core as af
        import sugarcode.modules.docking_studio.vina as vina
        fx = {"source": "fixture", "residues": [
            {"resnum": i, "resname": "ALA", "chain": "A", "ca": (i * 3.0, 0.0, 0.0), "bfactor": 10.0}
            for i in range(1, 15)]}
        monkeypatch.setattr(st, "fetch_alphafold", lambda i, offline=False: fx)
        monkeypatch.setattr(af, "_real_pockets", lambda res: [{"residues": [1, 2, 3, 4]}])
        monkeypatch.setattr(md, "resistance_scan", lambda seq, drugs, pocket_start=1: {"scan": True})
        monkeypatch.setattr(vina, "dock_vina_grid", lambda a, s: {"vina_score": -1.0, "estimated_dg_kcal_mol": -1.0})
        import sugarcode.bio.uniprot as up
        monkeypatch.setattr(up, "_get", lambda url, offline=False:
                            __import__("json").dumps({"features": features}).encode())

    def test_overlap_verdict(self, monkeypatch):
        self._setup(monkeypatch, [{"type": "Binding site",
                                   "location": {"start": {"value": 2}, "end": {"value": 3}}}])
        from sugarcode.modules.mutdock import structure_resistance_scan
        r = structure_resistance_scan("P99999", {"drug": "CC"})
        bv = r["binding_site_validation"]
        assert bv["pocket_residues_in_annotated_sites"] == 2
        assert "overlaps" in bv["verdict"]

    def test_no_overlap_honest_verdict(self, monkeypatch):
        self._setup(monkeypatch, [{"type": "Binding site",
                                   "location": {"start": {"value": 10}, "end": {"value": 12}}}])
        from sugarcode.modules.mutdock import structure_resistance_scan
        assert "does NOT overlap" in structure_resistance_scan("P99999", {"drug": "CC"})["binding_site_validation"]["verdict"]

    def test_no_features(self, monkeypatch):
        self._setup(monkeypatch, [])
        from sugarcode.modules.mutdock import structure_resistance_scan
        assert "no annotated BINDING" in structure_resistance_scan("P99999", {"drug": "CC"})["binding_site_validation"]["status"]
