"""Drop 21: true numbering, chain dedupe, HETATM filter, unified gnomAD evidence."""
import pytest


class TestTrueNumbering:
    def test_noncontiguous_resnums_label_correctly(self):
        from sugarcode.modules.mutdock.core import mutation_effect
        e = mutation_effect("TLIV", "CCO", 1, "I", resnums=[253, 315, 317, 400])
        assert e["mutation"] == "L315I"

    def test_scan_positions_use_resnums(self):
        from sugarcode.modules.mutdock.core import resistance_scan
        r = resistance_scan("TLIVK", {"drug": "CCO"}, resnums=[253, 315, 317, 400, 401])
        positions = {w["position"] for w in r["per_drug"]["drug"]["positions"]}
        assert positions == {253, 315, 317, 400, 401}

    def test_fallback_start_still_works(self):
        from sugarcode.modules.mutdock.core import resistance_scan
        r = resistance_scan("TLI", {"drug": "CCO"}, pocket_start=10)
        assert {w["position"] for w in r["per_drug"]["drug"]["positions"]} == {11, 12, 13}


class TestHetatmFilter:
    def _pdb(self):
        lines = ["ATOM      1  CA  ALA A   1       0.000   0.000   0.000  1.00 10.00           C"]
        # 3-atom additive (GOL) + 9-atom real ligand (LIG)
        for j in range(3):
            lines.append(f"HETATM{j+1:>5}  O1  GOL B  50    {j:8.3f}{0.0:8.3f}{0.0:8.3f}  1.00 10.00           O")
        for j in range(9):
            lines.append(f"HETATM{j+4:>5}  C1  LIG B  99    {j:8.3f}{5.0:8.3f}{0.0:8.3f}  1.00 10.00           C")
        return "\n".join(lines) + "\nEND\n"

    def test_additives_and_small_groups_excluded(self):
        from sugarcode.bio.structures import parse_pdb_hetatm
        ligs = parse_pdb_hetatm(self._pdb())
        names = [l["resname"] for l in ligs]
        assert "LIG" in names and "GOL" not in names


class TestUnifiedGnomADEvidence:
    def test_common_variant_is_benign_evidence(self, monkeypatch):
        from sugarcode.bio import gnomad, entrez
        monkeypatch.setattr(gnomad, "gene_constraint", lambda g, offline=False: {"gene": g, "lof_constrained": False})
        monkeypatch.setattr(gnomad, "variant_frequency", lambda v, dataset="gnomad_r4", offline=False:
                            {"variant_id": v, "present": True, "max_af": 0.716})
        monkeypatch.setattr(entrez, "clinvar_exact", lambda g, v, offline=False: [])
        from sugarcode.modules.openclinvar import interpret_variant_live
        r = interpret_variant_live("TP53", "c.215C>G", consequence="missense",
                                   variant_id="17-7676154-G-C")
        ev = [e for e in r["evidence"] if e["rule"] == "GNOMAD_FREQUENCY"][0]
        assert ev["weight"] == -0.8

    def test_absent_variant_weak_support(self, monkeypatch):
        from sugarcode.bio import gnomad, entrez
        monkeypatch.setattr(gnomad, "gene_constraint", lambda g, offline=False: {"gene": g, "lof_constrained": False})
        monkeypatch.setattr(gnomad, "variant_frequency", lambda v, dataset="gnomad_r4", offline=False:
                            {"variant_id": v, "present": False})
        monkeypatch.setattr(entrez, "clinvar_exact", lambda g, v, offline=False: [])
        from sugarcode.modules.openclinvar import interpret_variant_live
        r = interpret_variant_live("TP53", "c.818G>A", consequence="missense",
                                   variant_id="17-7674221-C-T")
        ev = [e for e in r["evidence"] if e["rule"] == "GNOMAD_FREQUENCY"][0]
        assert ev["weight"] == 0.2

    def test_no_variant_id_no_frequency_block(self, monkeypatch):
        from sugarcode.bio import gnomad, entrez
        monkeypatch.setattr(gnomad, "gene_constraint", lambda g, offline=False: {"gene": g, "lof_constrained": False})
        monkeypatch.setattr(entrez, "clinvar_exact", lambda g, v, offline=False: [])
        from sugarcode.modules.openclinvar import interpret_variant_live
        r = interpret_variant_live("TP53", "c.818G>A", consequence="missense")
        assert "gnomad_frequency" not in r
