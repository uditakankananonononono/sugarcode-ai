
# --- drop 11: openclinvar live ClinVar evidence --------------------------------
class TestOpenClinVarLive:
    def _fx(self):
        # recorded fixture: real ClinVar response shape for the 5382insC founder
        return [{"uid": "17637", "title": "NM_007294.4(BRCA1):c.5266dup (p.Gln1756fs)",
                 "significance": "Pathogenic", "review_status": "reviewed by expert panel",
                 "condition": "Hereditary breast ovarian cancer syndrome"}]

    def test_live_match_appends_weighted_evidence(self, monkeypatch):
        from sugarcode.bio import entrez
        monkeypatch.setattr(entrez, "clinvar_exact", lambda g, v, offline=False: self._fx())
        from sugarcode.modules.openclinvar import interpret_variant_live
        r = interpret_variant_live("BRCA1", "c.5266dup", consequence="frameshift")
        assert r["clinvar_live"]["status"] == "matched"
        assert r["clinvar_live"]["significance"] == "Pathogenic"
        lv = [e for e in r["evidence"] if e["rule"] == "CLINVAR_LIVE"][0]
        assert lv["weight"] > 0 and set(lv) == {"rule", "weight", "detail"}

    def test_near_miss_titles_rejected(self, monkeypatch):
        from sugarcode.bio import entrez
        fx = self._fx()  # c.5266dup title should NOT satisfy a query for c.68_69del
        monkeypatch.setattr(entrez, "clinvar_exact", lambda g, v, offline=False: fx)
        from sugarcode.modules.openclinvar import interpret_variant_live
        r = interpret_variant_live("BRCA1", "c.68_69del", consequence="frameshift")
        assert r["clinvar_live"]["status"].startswith("no live ClinVar entry")

    def test_conflicting_is_neutral(self, monkeypatch):
        from sugarcode.bio import entrez
        fx = [{"uid": "1", "title": "NM_007294.4(BRCA1):c.100A>G",
               "significance": "Conflicting classifications of pathogenicity",
               "review_status": "criteria provided", "condition": "x"}]
        monkeypatch.setattr(entrez, "clinvar_exact", lambda g, v, offline=False: fx)
        from sugarcode.modules.openclinvar import interpret_variant_live
        r = interpret_variant_live("BRCA1", "c.100A>G", consequence="missense")
        assert [e for e in r["evidence"] if e["rule"] == "CLINVAR_LIVE"][0]["weight"] == 0.0

    def test_lookup_failure_reported_not_fabricated(self, monkeypatch):
        from sugarcode.bio import entrez
        def boom(g, v, offline=False): raise RuntimeError("offline")
        monkeypatch.setattr(entrez, "clinvar_exact", boom)
        from sugarcode.modules.openclinvar import interpret_variant_live
        r = interpret_variant_live("BRCA1", "c.100A>G", consequence="missense")
        assert r["clinvar_live"]["status"].startswith("lookup failed")
        assert not any(e["rule"] == "CLINVAR_LIVE" for e in r["evidence"])

# --- drop 11: evofold real-structure dynamics ----------------------------------
class TestEvoFoldDynamics:
    def _pdb_fixture(self):
        lines = []
        for i in range(1, 21):
            x, y, z = i * 3.8, (i % 5) * 1.2, (i % 7) * 0.9
            lines.append(
                f"ATOM  {i:>5}  CA  ALA A{i:>4}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00 10.00           C")
        return "\n".join(lines) + "\nEND\n"

    def test_modes_and_hinges_from_fixture_pdb(self, monkeypatch):
        from sugarcode.bio import structures
        pdb_text = self._pdb_fixture().encode()
        meta = b'{"exptl": [{"method": "X-RAY DIFFRACTION"}], "rcsb_entry_info": {}, "struct": {"title": "fixture"}}'
        def fake_get(url, offline=False):
            return pdb_text if url.endswith(".pdb") else meta
        monkeypatch.setattr(structures, "_get", fake_get)
        from sugarcode.modules.evofold_4d.core import structure_dynamics
        r = structure_dynamics("1TST", chain="A", n_modes=4)
        assert r["structure"]["n_residues"] == 20
        assert r["structure"]["source"].startswith("RCSB")
        assert len(r["modes"]) == 4
        assert all(m["frequency"] > 0 for m in r["modes"])
        assert len(r["hinge_residues_real"]) == len(r["hinge_residues"])
        assert r["validation"]["pearson_r"] is None or -1 <= r["validation"]["pearson_r"] <= 1

    def test_failure_reported_not_fabricated(self, monkeypatch):
        from sugarcode.bio import structures
        def boom(url, offline=False): raise structures.StructureError("offline")
        monkeypatch.setattr(structures, "_get", boom)
        from sugarcode.modules.evofold_4d.core import structure_dynamics
        import pytest
        with pytest.raises(structures.StructureError):
            structure_dynamics("9ZZZ", chain="A")

# --- drop 11: chemgpt live ChEMBL similarity -----------------------------------
class TestChemGptSimilarity:
    def _fx(self):
        return [{"chembl_id": "CHEMBL25", "pref_name": "ASPIRIN",
                 "similarity": 100.0, "max_phase": 4, "smiles": "CC(=O)Oc1ccccc1C(=O)O"}]

    def test_known_drug_identified(self, monkeypatch):
        from sugarcode.bio import chembl
        monkeypatch.setattr(chembl, "similarity_search", lambda s, cutoff=80, limit=10, offline=False: self._fx())
        from sugarcode.modules.chemgpt_engine import similarity_check
        r = similarity_check("CC(=O)Oc1ccccc1C(=O)O")
        assert r["status"] == "ok"
        assert r["closest"]["pref_name"] == "ASPIRIN"
        assert r["novelty"] == "close analog of known compounds"
        assert r["approved_neighbors"][0]["max_phase"] == 4

    def test_no_hits_is_honest_novelty(self, monkeypatch):
        from sugarcode.bio import chembl
        monkeypatch.setattr(chembl, "similarity_search", lambda s, cutoff=80, limit=10, offline=False: [])
        from sugarcode.modules.chemgpt_engine import similarity_check
        r = similarity_check("c1ccc(C2CCCCN2)nn1")
        assert r["status"] == "ok" and r["closest"] is None
        assert "novel" in r["novelty"]

    def test_failure_reported_not_fabricated(self, monkeypatch):
        from sugarcode.bio import chembl
        def boom(s, cutoff=80, limit=10, offline=False): raise chembl.ChEMBLError("offline")
        monkeypatch.setattr(chembl, "similarity_search", boom)
        from sugarcode.modules.chemgpt_engine import similarity_check
        r = similarity_check("CCO")
        assert r["status"].startswith("lookup failed") and r["novelty"] == "unknown"
