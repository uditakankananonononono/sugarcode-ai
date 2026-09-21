"""Drop 26: 10-gene golden extension + AT-AC site-class detection (see
test_extended_splice.py), exon-skip consequence context, and UniProt
binding-annotation on outside-pocket organoid mutations."""
import pytest

import sugarcode.bio.splice as sp
from sugarcode.modules.deepsplice import live_splice_assessment


# --- (b) exon-skip consequence context -------------------------------------

def _jm(exons_spans, donors=None, acceptors=None):
    # plus-strand fixture map: genomic spans == cDNA layout
    exons = []
    n = 0
    for a, b in exons_spans:
        ln = b - a + 1
        exons.append({"cdna_start": n + 1, "cdna_end": n + ln, "length": ln})
        n += ln
    return {"status": "ok", "donors": donors or {}, "acceptors": acceptors or {},
            "sequence": "A" * 1000, "strand": 1, "cds_spans": exons_spans,
            "exons": exons, "source": "fixture"}


def test_donor_loss_inframe_exon_context(monkeypatch):
    # exon ending at c.212 is 78 nt (BRCA1 exon 5 shape) -> in-frame
    monkeypatch.setattr(sp, "junction_map", lambda gene, offline=False:
                        _jm([(1, 134), (135, 212), (213, 400)],
                            donors={212: "AAGGTAAGT"}))
    r = live_splice_assessment("GENE", "c.212+1G>A")
    assert r["status"] == "natural_site" and r["delta"] <= -0.15
    ec = r["exon_context"]
    assert ec["in_frame"] is True and ec["skipped_exon"]["length"] == 78
    assert "in-frame deletion" in ec["conditional_prediction"]
    assert "if skipping occurs" in ec["conditional_prediction"]  # conditional honesty


def test_donor_loss_frameshift_exon_context(monkeypatch):
    # MLH1 c.790+1 shape: skipped exon 113 nt -> frameshift
    monkeypatch.setattr(sp, "junction_map", lambda gene, offline=False:
                        _jm([(1, 677), (678, 790), (791, 1000)],
                            donors={790: "AAGGTAAGT"}))
    r = live_splice_assessment("GENE", "c.790+1G>A")
    ec = r["exon_context"]
    assert ec["in_frame"] is False and "frameshift" in ec["conditional_prediction"]


def test_acceptor_loss_skip_context_and_weak_call_has_none(monkeypatch):
    monkeypatch.setattr(sp, "junction_map", lambda gene, offline=False:
                        _jm([(1, 134), (135, 212), (213, 400)],
                            acceptors={135: "CCCTACCCTGCTAGT"}))  # real-convention AG at -2/-1
    r = live_splice_assessment("GENE", "c.135-1G>T")
    assert r["status"] == "natural_site"
    assert r["exon_context"]["skipped_exon"] == {"cdna_start": 135, "cdna_end": 212,
                                                 "length": 78}
    # a weak perturbation (delta > -0.15) carries NO exon context
    monkeypatch.setattr(sp, "junction_map", lambda gene, offline=False:
                        _jm([(1, 134), (135, 212), (213, 400)],
                            donors={212: "AAGGTAAGT"}))
    r2 = live_splice_assessment("GENE", "c.212+5G>C")  # +5 changes are mild
    assert r2["status"] == "natural_site" and "exon_context" not in r2


# --- (c) UniProt binding annotation on outside-pocket mutations -------------

def _combo_mocks(monkeypatch, sites):
    from sugarcode.bio import chembl, uniprot as up
    import sugarcode.bio.structures as st
    monkeypatch.setattr(chembl, "target_search", lambda g, offline=False: [
        {"chembl_id": "CHEMBL1862", "pref_name": "ABL1", "type": "SINGLE PROTEIN",
         "organism": "Homo sapiens"}])
    monkeypatch.setattr(chembl, "molecule_search", lambda n, offline=False:
                        {"chembl_id": "M1", "name": n, "max_phase": 4, "smiles": "CCO"})
    monkeypatch.setattr(chembl, "activities_for_molecule_target",
                        lambda m, t, offline=False: [{"standard_type": "IC50", "value_nM": 5.0,
                                                      "relation": "=", "assay_type": "B",
                                                      "pchembl": "8.3", "document_year": 2010}])
    monkeypatch.setattr(st, "ligand_pocket", lambda pdb, lig, chain=None, offline=False: {
        "pdb_id": pdb, "ligand": lig, "ligand_instances": 1, "radius_A": 6.0,
        "lining": [{"resname": "THR", "resnum": 315, "chain": "A", "ca": [0, 0, 0]}],
        "n_lining": 1, "source": "fixture"})
    if isinstance(sites, Exception):
        def boom(g, offline=False):
            raise sites
        monkeypatch.setattr(up, "binding_sites", boom)
    else:
        monkeypatch.setattr(up, "binding_sites", lambda g, offline=False: sites)


def test_outside_pocket_binding_annotation(monkeypatch):
    _combo_mocks(monkeypatch, {"status": "ok", "gene": "ABL1", "accession": "P00519",
                               "sites": [{"type": "Binding site", "begin": 248, "end": 256,
                                          "description": "ATP"}]})
    from sugarcode.modules.organoid_screen import screen_with_structure
    r = screen_with_structure("blood", ["drugA"], "ABL1", "1IEP", "STI",
                              mutations=["E255K", "D800N"])
    e255 = next(m for m in r["mutation_reports"] if m["mutation"] == "E255K")
    eff = e255["effects"]["drugA"]
    assert eff["status"] == "outside pocket"
    assert "P00519" in eff["binding_annotation"] and "248-256" in eff["binding_annotation"]
    assert eff["affinity_loss_fold"] == 1.0  # annotated, never re-scored
    d800 = next(m for m in r["mutation_reports"] if m["mutation"] == "D800N")
    assert "binding_annotation" not in d800["effects"]["drugA"]


def test_binding_annotation_fails_soft(monkeypatch):
    _combo_mocks(monkeypatch, RuntimeError("UniProt down"))
    from sugarcode.modules.organoid_screen import screen_with_structure
    r = screen_with_structure("blood", ["drugA"], "ABL1", "1IEP", "STI",
                              mutations=["E255K"])
    eff = r["mutation_reports"][0]["effects"]["drugA"]
    assert eff["status"] == "outside pocket" and "binding_annotation" not in eff


def test_uniprot_binding_sites_parsing(monkeypatch):
    from sugarcode.bio import uniprot
    monkeypatch.setattr(uniprot, "search", lambda g, offline=False: {
        "accession": "P00519", "features": [
            {"type": "Binding site", "begin": 248, "end": 256, "description": ""},
            {"type": "Active site", "begin": 363, "end": 363, "description": "Proton acceptor"},
            {"type": "Site", "begin": 26, "end": 27, "description": "Breakpoint"}]})
    r = uniprot.binding_sites("ABL1")
    assert r["status"] == "ok" and r["accession"] == "P00519"
    assert len(r["sites"]) == 2  # Binding site + Active site, NOT generic Site
    monkeypatch.setattr(uniprot, "search", lambda g, offline=False: None)
    assert uniprot.binding_sites("NOGENE")["status"] == "no UniProt entry"
