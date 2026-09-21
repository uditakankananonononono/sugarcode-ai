"""Drop 14: Vina-form scoring, Shrake-Rupley SASA, real interface areas."""
import math
import pytest


class TestVinaTerms:
    def test_weights_are_trott_olson(self):
        from sugarcode.modules.docking_studio.vina import W
        assert W == {"gauss1": -0.0356, "gauss2": -0.00516, "repulsion": 0.840,
                     "hydrophobic": -0.0351, "hbond": -0.587, "torsion": 0.0585}

    def test_clash_is_unfavorable(self):
        from sugarcode.modules.docking_studio.vina import vina_pair_terms
        t = vina_pair_terms(1.0, "C", "C")  # d = -2.8 -> repulsion 7.84
        assert t["repulsion"] == pytest.approx(7.84)

    def test_hbond_ramp(self):
        from sugarcode.modules.docking_studio.vina import vina_pair_terms
        assert vina_pair_terms(3.4, "O", "N")["hbond"] == pytest.approx(1 / 7, abs=1e-3)
        assert vina_pair_terms(3.5, "O", "N")["hbond"] == 0.0
        assert vina_pair_terms(2.7, "O", "N")["hbond"] == 1.0  # d = -0.8 < -0.7

    def test_hydrophobic_ramp(self):
        from sugarcode.modules.docking_studio.vina import vina_pair_terms
        assert vina_pair_terms(4.8, "C", "C")["hydrophobic"] == pytest.approx(0.5)
        assert vina_pair_terms(4.8, "C", "O")["hydrophobic"] == 0.0  # not both hydrophobic

    def test_far_pairs_zero(self):
        from sugarcode.modules.docking_studio.vina import vina_pair_terms
        assert all(v == 0.0 for v in vina_pair_terms(20.0, "C", "C").values())

    def test_grid_beats_clashing_placement(self):
        from sugarcode.modules.docking_studio.vina import dock_vina_grid
        pocket = [{"element": "C", "xyz": (0, 0, 0)}, {"element": "C", "xyz": (4, 0, 0)},
                  {"element": "C", "xyz": (0, 4, 0)}, {"element": "C", "xyz": (4, 4, 0)}]
        r = dock_vina_grid(pocket, "CCCC", grid_step=2.0, n_steps=3)
        # a clashing pose (repulsion > 0) must never win over the best found
        assert r["terms"]["repulsion"] < 5.0
        assert r["limits"]  # honest limits always attached


class TestSASA:
    def test_isolated_atom_analytic(self):
        from sugarcode.bio.structures import sasa_shrake_rupley
        r = sasa_shrake_rupley([{"element": "C", "xyz": (0, 0, 0)}])
        assert r["total_A2"] == pytest.approx(4 * math.pi * 3.1 ** 2, abs=0.2)

    def test_contact_buries_area(self):
        from sugarcode.bio.structures import sasa_shrake_rupley
        far = sasa_shrake_rupley([{"element": "C", "xyz": (0, 0, 0)},
                                  {"element": "C", "xyz": (20, 0, 0)}])
        close = sasa_shrake_rupley([{"element": "C", "xyz": (0, 0, 0)},
                                    {"element": "C", "xyz": (2, 0, 0)}])
        assert close["total_A2"] < far["total_A2"]

    def test_interface_from_fixture(self, monkeypatch):
        from sugarcode.bio import structures
        # two 3-residue chains 6 A apart - small but positive buried area
        lines = []
        n = 0
        for ch, x0 in [("A", 0.0), ("B", 6.0)]:
            for i in range(3):
                n += 1
                lines.append(f"ATOM  {n:>5}  CA  ALA {ch}{i+1:>4}    "
                             f"{x0:8.3f}{i*3.8:8.3f}{0.0:8.3f}  1.00 10.00           C")
        pdb = "\n".join(lines) + "\nEND\n"
        monkeypatch.setattr(structures, "_get", lambda url, offline=False: pdb.encode())
        r = structures.interface_area("9FIX", "A", "B")
        assert r["buried_surface_area_A2"] > 0
        assert r["sasa_complex"] < r["sasa_A"] + r["sasa_B"]

    def test_missing_chain_raises(self, monkeypatch):
        from sugarcode.bio import structures
        pdb = "ATOM      1  CA  ALA A   1       0.000   0.000   0.000  1.00 10.00           C\nEND\n"
        monkeypatch.setattr(structures, "_get", lambda url, offline=False: pdb.encode())
        with pytest.raises(structures.StructureError):
            structures.interface_area("9FIX", "A", "Z")


# --- drop 15: neohunter live UniProt -------------------------------------------
class TestNeoHunterLive:
    SEQ = "M" + "E" * 271 + "R" + "A" * 120  # 392 aa, R at position 273

    def _fx_record(self):
        return {"accession": "P04637", "sequence": self.SEQ, "length": len(self.SEQ),
                "features": [{"type": "Natural variant",
                              "description": "in LFS; germline mutation; somatic",
                              "begin": 273, "end": 273},
                             {"type": "Mutagenesis", "description": "loss of function",
                              "begin": 273, "end": 273},
                             {"type": "Region", "description": "unrelated",
                              "begin": 100, "end": 120}]}

    def test_live_scan_validates_and_attaches_priors(self, monkeypatch):
        from sugarcode.bio import uniprot
        monkeypatch.setattr(uniprot, "search", lambda g, organism_id=9600, offline=False: self._fx_record())
        from sugarcode.modules.neohunter import find_neoantigens_live
        r = find_neoantigens_live("TP53", 273, "H")
        assert r["mutation"] == "R273H"
        assert r["wt_residue_validated"] is True
        assert r["variant_prior_count"] == 2  # Region feature excluded
        assert len(r["candidates"]) == 9  # nine 9-mers span the mutation
        assert all("H" in c["peptide"] for c in r["candidates"])

    def test_position_out_of_range_refused(self, monkeypatch):
        from sugarcode.bio import uniprot
        monkeypatch.setattr(uniprot, "search", lambda g, organism_id=9600, offline=False: self._fx_record())
        from sugarcode.modules.neohunter import find_neoantigens_live
        import pytest as _pt
        with _pt.raises(ValueError):
            find_neoantigens_live("TP53", 999, "H")

    def test_lookup_failure_raises_not_fabricates(self, monkeypatch):
        from sugarcode.bio import uniprot
        def boom(g, organism_id=9600, offline=False): raise uniprot.UniProtError("offline")
        monkeypatch.setattr(uniprot, "search", boom)
        from sugarcode.modules.neohunter import find_neoantigens_live
        import pytest as _pt
        with _pt.raises(uniprot.UniProtError):
            find_neoantigens_live("TP53", 273, "H")
