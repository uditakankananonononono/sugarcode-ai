"""Drop 20: co-crystal ligand pockets, UniProt feature awareness, joint case view."""
import pytest


class TestLigandPocket:
    def _pdb_fixture(self):
        # 4-residue protein chain + a 5-atom ligand 'LIG' near residues 2-3
        lines = []
        for i in range(1, 5):
            lines.append(f"ATOM  {i:>5}  CA  ALA A{i:>4}    "
                         f"{i * 4.0:8.3f}{0.0:8.3f}{0.0:8.3f}  1.00 10.00           C")
        for j in range(9):
            lines.append(f"HETATM{j+1:>5}  C1  LIG B  99    "
                         f"{8.0 + j * 0.5:8.3f}{1.0:8.3f}{1.0:8.3f}  1.00 10.00           C")
        return "\n".join(lines) + "\nEND\n"

    def test_pocket_from_cocrystal(self, monkeypatch):
        from sugarcode.bio import structures
        monkeypatch.setattr(structures, "_get", lambda url, offline=False: self._pdb_fixture().encode())
        r = structures.ligand_pocket("9LIG", "LIG", radius=3.5)
        resnums = {x["resnum"] for x in r["lining"]}
        assert 2 in resnums and 3 in resnums  # near the ligand
        assert 1 not in resnums or 4 not in resnums  # far end excluded
        assert r["ligand_instances"] == 1

    def test_missing_ligand_lists_available(self, monkeypatch):
        from sugarcode.bio import structures
        monkeypatch.setattr(structures, "_get", lambda url, offline=False: self._pdb_fixture().encode())
        with pytest.raises(structures.StructureError) as e:
            structures.ligand_pocket("9LIG", "ATP")
        assert "LIG" in str(e.value)

    def test_mutdock_ligand_path(self, monkeypatch):
        from sugarcode.modules.mutdock import core as md
        import sugarcode.bio.structures as st
        fx = {"source": "fixture", "residues": [
            {"resnum": i, "resname": "ALA", "chain": "A", "ca": (i * 3.0, 0.0, 0.0), "bfactor": 10.0}
            for i in range(1, 12)]}
        monkeypatch.setattr(st, "fetch_pdb", lambda i, offline=False: fx)
        monkeypatch.setattr(st, "ligand_pocket", lambda pdb, lig, radius=6.0, chain=None, offline=False:
                            {"pdb_id": pdb, "ligand": lig, "ligand_instances": 1, "radius_A": radius,
                             "n_lining": 3, "lining": fx["residues"][2:5], "source": "fixture"})
        import sugarcode.modules.docking_studio.vina as vina
        monkeypatch.setattr(vina, "dock_vina_grid", lambda a, s: {"vina_score": -1.0, "estimated_dg_kcal_mol": -1.0})
        monkeypatch.setattr(md, "resistance_scan", lambda seq, drugs, pocket_start=1, resnums=None: {"scan": True})
        r = md.structure_resistance_scan("1FIX", {"drug": "CC"}, ligand_resname="LIG")
        assert "co-crystal ligand LIG" in r["structure"]["pocket_source"]


class TestFeatureAwareness:
    def test_natural_variant_caveat(self, monkeypatch):
        from sugarcode.modules.mutdock import core as md
        import sugarcode.bio.structures as st
        import sugarcode.modules.alpha_fold_ui.core as af
        import sugarcode.modules.docking_studio.vina as vina
        import sugarcode.bio.uniprot as up
        fx = {"source": "fixture", "residues": [
            {"resnum": i, "resname": "ALA", "chain": "A", "ca": (i * 3.0, 0.0, 0.0), "bfactor": 10.0}
            for i in range(1, 15)]}
        monkeypatch.setattr(st, "fetch_alphafold", lambda i, offline=False: fx)
        monkeypatch.setattr(af, "_real_pockets", lambda res: [{"residues": [3, 4]}])
        monkeypatch.setattr(md, "resistance_scan", lambda seq, drugs, pocket_start=1, resnums=None: {"scan": True})
        monkeypatch.setattr(vina, "dock_vina_grid", lambda a, s: {"vina_score": -1.0, "estimated_dg_kcal_mol": -1.0})
        feats = [{"type": "Natural variant", "description": "tolerated",
                  "location": {"start": {"value": 3}, "end": {"value": 3}}}]
        monkeypatch.setattr(up, "_get", lambda url, offline=False:
                            __import__("json").dumps({"features": feats}).encode())
        r = md.structure_resistance_scan("P99999", {"drug": "CC"})
        bv = r["binding_site_validation"]
        assert bv["natural_variants_in_pocket"][0]["resnum"] == 3
        assert "tolerated" in bv["caveat"]


class TestJointCaseView:
    def test_lead_when_gene_in_differential(self, monkeypatch):
        from sugarcode.modules import infinite_diagnosis as idg
        from sugarcode.modules.rarenet_ai import core as rn
        monkeypatch.setattr(rn, "diagnose", lambda symptoms: {
            "candidates": [{"disease": "phenylketonuria", "confidence": 0.9, "genes": ["PAH"]}]})
        monkeypatch.setattr(rn, "variant_evidence_panel", lambda variants, offline=False: {
            "panel": [{"gene": "PAH", "hgvs": "c.1A>G", "support_score": 2.5,
                       "evidence_class": "strong support"}],
            "disclaimer": "not a diagnosis"})
        r = idg.core.joint_case_view(["seizures"], [{"gene": "PAH"}])
        assert r["top_hypothesis"]["lead_hypothesis"] is True
        assert r["top_hypothesis"]["gene_named_in_symptom_differential"] is True

    def test_no_lead_when_gene_unrelated(self, monkeypatch):
        from sugarcode.modules import infinite_diagnosis as idg
        from sugarcode.modules.rarenet_ai import core as rn
        monkeypatch.setattr(rn, "diagnose", lambda symptoms: {
            "candidates": [{"disease": "cystic_fibrosis", "confidence": 0.9, "genes": ["CFTR"]}]})
        monkeypatch.setattr(rn, "variant_evidence_panel", lambda variants, offline=False: {
            "panel": [{"gene": "PAH", "hgvs": "c.1A>G", "support_score": 2.5,
                       "evidence_class": "strong support"}],
            "disclaimer": "not a diagnosis"})
        r = idg.core.joint_case_view(["chronic cough"], [{"gene": "PAH"}])
        assert r["top_hypothesis"] is None

    def test_symptom_space_normalization(self):
        from sugarcode.modules.rarenet_ai.core import diagnose
        r = diagnose(["intellectual disability", "musty odor"])  # spaces, not underscores
        assert any("phenylketonuria" == c["disease"] for c in r["candidates"])
