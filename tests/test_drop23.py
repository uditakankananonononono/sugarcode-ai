"""Drop 23: cryptic-site activation + per-compound (allosteric) pockets."""
import json
from pathlib import Path

from sugarcode.modules.deepsplice import cryptic_scan
from sugarcode.modules.organoid_screen import screen_with_structure


# --- cryptic_scan ----------------------------------------------------------

def test_new_consensus_site_is_strong_finding():
    ref = "AAATTTCCCATG" + "AAGAAAAGT" + "TTTCCCAAATTT"   # +2 C breaks GT
    alt = ref[:12] + "AAGGTAAGT" + ref[21:]               # full consensus donor
    r = cryptic_scan(ref, alt)
    new = [f for f in r["strong_findings"] if f["site_type"] == "donor"]
    assert new and new[0]["alt_score"] > 0.9
    assert "NEW cryptic donor" in r["verdict"]


def test_single_snp_context_gives_weak_only():
    ref = "AAATTTCCCATGAAGGTGAGTTTTCCCAAATTT"
    alt = ref[:15] + "C" + ref[16:]
    r = cryptic_scan(ref, alt)
    assert r["strong_findings"] == []
    assert "not discriminating evidence" in r["verdict"] or "no cryptic" in r["verdict"]


def test_cftr_literature_cryptic_donor_detected():
    """Published golden: CFTR c.3718-2477C>T (3849+10kbC>T) creates a cryptic
    donor -> 84-nt pseudoexon. Real NG_016465.4 context, vendored."""
    fx = json.loads(Path("tests/fixtures/cftr_cryptic_golden.json").read_text())
    r = cryptic_scan(fx["ref_context"], fx["alt_context"])
    new = [f for f in r["strong_findings"] if f["site_type"] == "donor"]
    assert new, r["verdict"]
    assert new[0]["alt_score"] >= 0.9
    assert new[0]["ref_score"] < 0.75


# --- per-compound pockets ---------------------------------------------------

def _patch_combo(monkeypatch):
    from sugarcode.bio import chembl
    import sugarcode.bio.structures as st
    monkeypatch.setattr(chembl, "target_search", lambda g, offline=False: [
        {"chembl_id": "T", "pref_name": "ABL1", "type": "SINGLE PROTEIN",
         "organism": "Homo sapiens"}])
    mols = {"atpDrug": {"chembl_id": "M1", "name": "atpDrug", "max_phase": 4, "smiles": "CCO"},
            "alloDrug": {"chembl_id": "M2", "name": "alloDrug", "max_phase": 4, "smiles": "CCN"}}
    monkeypatch.setattr(chembl, "molecule_search", lambda n, offline=False: mols.get(n))
    monkeypatch.setattr(chembl, "activities_for_molecule_target",
                        lambda m, t, offline=False: [{"standard_type": "IC50", "value_nM": 10.0,
                                                      "relation": "=", "assay_type": "B",
                                                      "pchembl": "8", "document_year": 2020}])
    def fake_pocket(pdb, lig, chain=None, offline=False):
        if lig == "ATP":
            lining = [{"resname": "THR", "resnum": 315, "chain": "A", "ca": [0, 0, 0]},
                      {"resname": "TYR", "resnum": 253, "chain": "A", "ca": [1, 0, 0]}]
        else:  # allosteric ligand: gatekeeper not in lining; structure offset +19
            lining = [{"resname": "LEU", "resnum": 360, "chain": "A", "ca": [0, 0, 0]},
                      {"resname": "VAL", "resnum": 468, "chain": "A", "ca": [1, 0, 0]}]
        return {"pdb_id": pdb, "ligand": lig, "ligand_instances": 1, "radius_A": 6.0,
                "lining": lining, "n_lining": len(lining), "source": "fixture"}
    monkeypatch.setattr(st, "ligand_pocket", fake_pocket)
    from sugarcode.bio import uniprot as up
    monkeypatch.setattr(up, "binding_sites", lambda g, offline=False:
                        {"status": "no UniProt entry", "gene": g})


def test_allosteric_override_changes_resistance_call(monkeypatch):
    _patch_combo(monkeypatch)
    r = screen_with_structure("colon", ["atpDrug", "alloDrug"], "ABL1", "1ATP", "ATP",
                              mutations=["T315I"],
                              pockets={"alloDrug": {"pdb_id": "5ALO", "ligand": "ALO",
                                                    "resnum_offset": 19}})
    eff = r["mutation_reports"][0]["effects"]
    assert eff["atpDrug"]["status"] == "in pocket"
    assert eff["atpDrug"]["affinity_loss_fold"] != 1.0
    # allosteric drug: gatekeeper (mapped 315 -> structure 334) outside its lining
    assert eff["alloDrug"]["status"] == "outside pocket"
    assert eff["alloDrug"]["affinity_loss_fold"] == 1.0
    assert "#334" in eff["alloDrug"]["detail"]
    by = {x["compound"]: x for x in r["ranking"]}
    assert by["alloDrug"]["resistance_fold"] == 1.0
    assert by["atpDrug"]["resistance_fold"] != 1.0
    assert r["structure"]["per_compound_pockets"]["alloDrug"] == "5ALO:ALO"


def test_offset_wrong_numbering_fails_loudly(monkeypatch):
    """Without the offset, a 1a-numbered structure maps T315 to a proline -
    wt mismatch must be named, never silently scored."""
    _patch_combo(monkeypatch)
    r = screen_with_structure("colon", ["alloDrug"], "ABL1", "1ATP", "ATP",
                              mutations=["T315I"],
                              pockets={"alloDrug": {"pdb_id": "5ALO", "ligand": "ALO"}})
    st = r["mutation_reports"][0]["effects"]["alloDrug"]
    assert st["status"] in ("outside pocket", "wt mismatch")
    assert st["affinity_loss_fold"] == 1.0
