"""Drop 22: real splice PWM data, ClinVar star tiers, organoid live combo screen."""
import json
from pathlib import Path

import pytest

from sugarcode.bio import splice as splice_mod
from sugarcode.modules import openclinvar
from sugarcode.modules.openclinvar import clinvar_stars, interpret_variant_live
from sugarcode.modules.organoid_screen import screen_with_structure


# --- real splice PWM data -------------------------------------------------

DATA = Path("src/sugarcode/bio/data/splice_sites")


def test_splice_data_files_and_provenance():
    for f in ("donor_pwm.json", "acceptor_pwm.json", "junctions.tsv", "PROVENANCE.md"):
        assert (DATA / f).exists(), f
    prov = (DATA / "PROVENANCE.md").read_text()
    assert "RefSeqGene" in prov and "2026-09-21" in prov


def test_learned_pwm_matches_published_consensus():
    dp = splice_mod.donor_pwm(); ap = splice_mod.acceptor_pwm()
    assert len(dp) == 9 and len(ap) == 15
    # donor +1/+2 are essentially invariant GT
    assert dp[3]["G"] > 0.95 and dp[4]["T"] > 0.95
    # acceptor -2/-1 are essentially invariant AG
    assert ap[12]["A"] > 0.95 and ap[13]["G"] > 0.95
    # acceptor has a polypyrimidine tract (T-rich upstream)
    assert sum(col["T"] for col in ap[:10]) / 10 > 0.4


def test_junctions_tsv_is_canonical_filtered_real_data():
    lines = (DATA / "junctions.tsv").read_text().splitlines()[1:]
    assert len(lines) == 1260
    canon = [l for l in lines if l.endswith("\t1")]
    assert len(canon) == 1215
    genes = {l.split("\t")[0] for l in lines}
    assert "BRCA1" in genes and "DMD" in genes and len(genes) >= 25


# --- ClinVar star tiers ----------------------------------------------------

@pytest.mark.parametrize("status,stars", [
    ("practice guideline", 4),
    ("reviewed by expert panel", 3),
    ("criteria provided, multiple submitters, no conflicts", 2),
    ("criteria provided, single submitter", 1),
    ("criteria provided, conflicting classifications", 1),
    ("no assertion criteria provided", 0),
    ("no classification provided", 0),
    (None, 0),
])
def test_clinvar_star_tiers(status, stars):
    assert clinvar_stars(status) == stars


def _fake_clinvar(monkeypatch, sig, review):
    from sugarcode.bio import entrez, gnomad
    monkeypatch.setattr(gnomad, "gene_constraint", lambda g, offline=False: {"lof_constrained": False})
    monkeypatch.setattr(entrez, "clinvar_exact", lambda g, v, offline=False: [
        {"uid": "1", "title": f"NM_000000.1({g}):{v}", "significance": sig,
         "review_status": review, "condition": "x"}])


def test_star_tier_weights_in_evidence(monkeypatch):
    _fake_clinvar(monkeypatch, "Pathogenic", "reviewed by expert panel")
    r = interpret_variant_live("GENE", "c.1+1G>A", consequence="splice_disruption")
    ev = next(e for e in r["evidence"] if e["rule"] == "CLINVAR_LIVE")
    assert ev["weight"] == 0.8 and r["clinvar_live"]["stars"] == 3

    _fake_clinvar(monkeypatch, "Pathogenic", "criteria provided, single submitter")
    r = interpret_variant_live("GENE", "c.1+1G>A", consequence="splice_disruption")
    ev = next(e for e in r["evidence"] if e["rule"] == "CLINVAR_LIVE")
    assert ev["weight"] == 0.3 and r["clinvar_live"]["stars"] == 1

    _fake_clinvar(monkeypatch, "Benign", "practice guideline")
    r = interpret_variant_live("GENE", "c.1+1G>A", consequence="splice_disruption")
    ev = next(e for e in r["evidence"] if e["rule"] == "CLINVAR_LIVE")
    assert ev["weight"] == -1.0 and r["clinvar_live"]["stars"] == 4


# --- organoid live combo screen -------------------------------------------

def test_combo_screen_live_axes(monkeypatch):
    from sugarcode.bio import chembl
    import sugarcode.modules.organoid_screen.core as core_mod
    import sugarcode.bio.structures as st
    monkeypatch.setattr(chembl, "target_search", lambda g, offline=False: [
        {"chembl_id": "CHEMBL1862", "pref_name": "ABL1", "type": "SINGLE PROTEIN",
         "organism": "Homo sapiens"}])
    mols = {"drugA": {"chembl_id": "M1", "name": "drugA", "max_phase": 4, "smiles": "CCO"},
            "drugB": {"chembl_id": "M2", "name": "drugB", "max_phase": 2, "smiles": "c1ccccc1"}}
    monkeypatch.setattr(chembl, "molecule_search", lambda n, offline=False: mols.get(n))
    acts = {"M1": [{"standard_type": "IC50", "value_nM": 5.0, "relation": "=",
                    "assay_type": "B", "pchembl": "8.3", "document_year": 2010}],
            "M2": [{"standard_type": "Ki", "value_nM": 500.0, "relation": "=",
                    "assay_type": "B", "pchembl": "6.3", "document_year": 2011}]}
    monkeypatch.setattr(chembl, "activities_for_molecule_target",
                        lambda m, t, offline=False: acts.get(m, []))
    lining = [{"resname": "THR", "resnum": 315, "chain": "A", "ca": [0, 0, 0]},
              {"resname": "TYR", "resnum": 253, "chain": "A", "ca": [1, 0, 0]},
              {"resname": "GLU", "resnum": 286, "chain": "A", "ca": [2, 0, 0]}]
    monkeypatch.setattr(st, "ligand_pocket", lambda pdb, lig, chain=None, offline=False: {
        "pdb_id": pdb, "ligand": lig, "ligand_instances": 1, "radius_A": 6.0,
        "lining": lining, "n_lining": len(lining), "source": "fixture"})

    r = screen_with_structure("colon", ["drugA", "drugB", "unknownDrug"],
                              "ABL1", "1IEP", "STI", mutations=["T315I", "D800N"])
    assert r["chembl_target"]["chembl_id"] == "CHEMBL1862"
    assert r["structure"]["n_lining"] == 3
    by = {x["compound"]: x for x in r["ranking"]}
    assert by["unknownDrug"]["status"].startswith("no ChEMBL")
    # T315I in pocket: both drugs get a resistance fold on top of ChEMBL potency
    t315 = next(m for m in r["mutation_reports"] if m["mutation"] == "T315I")
    assert t315["status"] == "in pocket"
    assert set(t315["effects"]) == {"drugA", "drugB"}
    # fold must equal the mutdock mutation_effect on the same pocket, and
    # effective IC50 must be ChEMBL potency x fold - the combo is the point
    from sugarcode.modules.mutdock.core import mutation_effect
    e = mutation_effect("TYE", "CCO", 0, "I", resnums=[315, 253, 286], drug_name="drugA")
    assert by["drugA"]["wt_potency_nM"] == 5.0
    assert by["drugA"]["resistance_fold"] == e["affinity_change_fold"]
    assert by["drugA"]["effective_ic50_uM"] == round(5.0 * e["affinity_change_fold"] / 1000, 4)
    assert by["drugB"]["wt_potency_nM"] == 500.0
    # D800N outside pocket: named, not silently dropped
    d800 = next(m for m in r["mutation_reports"] if m["mutation"] == "D800N")
    assert d800["status"] == "outside co-crystal pocket"
    # hit is the most potent compound after adjustment
    assert r["hit"] in ("drugA", "drugB")


def test_combo_wt_mismatch_named(monkeypatch):
    from sugarcode.bio import chembl
    import sugarcode.bio.structures as st
    monkeypatch.setattr(chembl, "target_search", lambda g, offline=False: [
        {"chembl_id": "T", "pref_name": "x", "type": "SINGLE PROTEIN", "organism": "Homo sapiens"}])
    monkeypatch.setattr(chembl, "molecule_search", lambda n, offline=False:
                        {"chembl_id": "M1", "name": n, "max_phase": 1, "smiles": "CCO"})
    monkeypatch.setattr(chembl, "activities_for_molecule_target",
                        lambda m, t, offline=False: [{"standard_type": "IC50", "value_nM": 1.0,
                                                      "relation": "=", "assay_type": "B",
                                                      "pchembl": "9", "document_year": 2020}])
    monkeypatch.setattr(st, "ligand_pocket", lambda pdb, lig, chain=None, offline=False: {
        "pdb_id": pdb, "ligand": lig, "ligand_instances": 1, "radius_A": 6.0,
        "lining": [{"resname": "THR", "resnum": 315, "chain": "A", "ca": [0, 0, 0]}],
        "n_lining": 1, "source": "fixture"})
    r = screen_with_structure("colon", ["drugA"], "ABL1", "1IEP", "STI", mutations=["A315I"])
    assert r["mutation_reports"][0]["status"] == "wt mismatch"
