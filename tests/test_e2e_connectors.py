"""End-to-end workflow: structure -> pocket -> dock -> report, exercising the
connectors together (transport monkeypatched with recorded fixtures)."""
import json
import pytest

from sugarcode.bio import structures, entrez, uniprot
from sugarcode.modules.alpha_fold_ui import analyze_real_structure
from sugarcode.modules.docking_studio import dock_into_structure
from sugarcode.modules.gene_analysis import live_gene_profile

def _pdb_rows():
    rows, rn = [], 1
    for i in range(30):
        rows.append(f"ATOM  {rn:5d}  CA  ALA A{rn:4d}    {20.0*i:8.3f}{0.0:8.3f}{0.0:8.3f}  1.00 80.00           C  ")
        rn += 1
    for i in range(12):
        rows.append(f"ATOM  {rn:5d}  CA  SER A{rn:4d}    {3.0*(i%3):8.3f}{3.0*((i//3)%2):8.3f}{3.0*(i//6):8.3f}  1.00 80.00           C  ")
        rn += 1
    rows.append("END")
    return ("\n".join(rows) + "\n").encode()

ENTRY = json.dumps({"exptl": [{"method": "X-RAY DIFFRACTION"}],
                    "rcsb_entry_info": {"resolution_combined": [1.9]},
                    "struct": {"title": "e2e fixture"}}).encode()
ESEARCH = json.dumps({"esearchresult": {"idlist": ["7157"]}}).encode()
ESUMMARY = json.dumps({"result": {"uids": ["7157"], "7157": {
    "name": "TP53", "description": "tumor protein p53", "chromosome": "17",
    "maplocation": "17p13.1", "otheraliases": "P53"}}}).encode()
UNIPROT = json.dumps({"results": [{
    "primaryAccession": "P04637", "uniProtkbId": "P53_HUMAN",
    "proteinDescription": {"recommendedName": {"fullName": {"value": "p53"}}},
    "organism": {"scientificName": "Homo sapiens"},
    "sequence": {"length": 393, "molWeight": 43653, "value": "MEEPQSDPSV"},
    "features": [], "uniProtKBCrossReferences": [], "comments": []}]}).encode()


@pytest.fixture(autouse=True)
def fake_all_transport(monkeypatch, tmp_path):
    monkeypatch.setattr(structures, "CACHE_DIR", tmp_path / "s")
    monkeypatch.setattr(entrez, "CACHE_DIR", tmp_path / "e")
    monkeypatch.setattr(uniprot, "CACHE_DIR", tmp_path / "u")

    def fake_struct(url, offline=False, retries=3):
        return _pdb_rows() if "files.rcsb" in url else ENTRY

    def fake_entrez(path, params, offline=False, retries=3):
        return ESUMMARY if "esummary" in path else ESEARCH

    def fake_uniprot(url, offline=False, retries=3):
        return UNIPROT

    monkeypatch.setattr(structures, "_get", fake_struct)
    monkeypatch.setattr(entrez, "_get", fake_entrez)
    monkeypatch.setattr(uniprot, "_get", fake_uniprot)


def test_structure_to_pocket_to_dock_pipeline():
    # step 1: gene grounding
    profile = live_gene_profile("TP53")
    assert profile["sources"]["uniprot"]["accession"] == "P04637"
    # step 2: structure analysis on the experimental structure
    struct = analyze_real_structure("1e2e")
    assert struct["n_residues"] == 42
    assert struct["pockets"], "dense SER ball must be found"
    # step 3: dock a ligand into the detected pocket
    result = dock_into_structure("1e2e", "c1ccncc1")
    assert result["structure"]["resolution_A"] == 1.9
    assert result["pocket"]["n_pockets_found"] >= 1
    assert result["binding_dg_kcal_mol"] < 0
    # step 4: the report chain is complete and provenance-labeled
    assert result["structure"]["source"] == "RCSB PDB (live)"
    assert "screening proxy" in result["scoring_note"]
