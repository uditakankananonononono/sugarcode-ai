import json
import pytest

from sugarcode.bio import chembl
from sugarcode.modules.neodti_engine import repurposing_scan_live, live_validation

MOL_SIROLIMUS = json.dumps({"molecules": [{
    "molecule_chembl_id": "CHEMBL413", "pref_name": "SIROLIMUS",
    "max_phase": 4, "molecule_structures": {"canonical_smiles": "C..."}}]}).encode()
ACT_MTOR = json.dumps({"activities": [
    {"molecule_chembl_id": "CHEMBL413", "standard_type": "IC50",
     "standard_value": "0.1", "standard_units": "nM", "standard_relation": "=",
     "assay_type": "B", "pchembl_value": "10.0", "document_year": 2019},
    {"molecule_chembl_id": "CHEMBL999", "standard_type": "IC50",
     "standard_value": "500", "standard_units": "nM", "standard_relation": "=",
     "assay_type": "B", "pchembl_value": "6.3", "document_year": 2018}]}).encode()
EMPTY = json.dumps({"molecules": []}).encode()


@pytest.fixture(autouse=True)
def fake_transport(monkeypatch, tmp_path):
    monkeypatch.setattr(chembl, "CACHE_DIR", tmp_path / "c")

    def fake_get(url, offline=False, retries=3):
        if offline:
            raise chembl.ChEMBLError("offline")
        if "molecule.json" in url and "sirolimus" in url:
            return json.loads(MOL_SIROLIMUS)
        if "molecule.json" in url:
            return json.loads(EMPTY)
        if "activity.json" in url:
            return json.loads(ACT_MTOR)
        raise AssertionError(url)

    monkeypatch.setattr(chembl, "_get", fake_get)


def test_activities_sorted_and_typed():
    acts = chembl.activities_for_target("CHEMBL2842")
    assert acts[0]["value_nM"] == 0.1
    assert acts[0]["standard_type"] == "IC50"


def test_live_validation_finds_measured_potency():
    cands = [{"drug": "rapamycin", "therapeutic_resilience_index": 0.5,
              "paths": [{"target": "mTOR", "pathway": "growth_signaling"}]}]
    out = live_validation(cands)
    ch = out[0]["chembl"]
    assert ch["status"] == "live"
    assert ch["queried_as"] == "sirolimus"       # INN alias applied, documented
    assert ch["molecule_chembl_id"] == "CHEMBL413"
    assert ch["best_measured_potency"]["value_nM"] == 0.1
    assert ch["best_measured_potency"]["target_chembl_id"] == "CHEMBL2842"


def test_live_validation_unknown_molecule_reported():
    cands = [{"drug": "aspirin", "therapeutic_resilience_index": 0.5,
              "paths": [{"target": "COX2", "pathway": "inflammation"}]}]
    out = live_validation(cands)
    assert out[0]["chembl"]["status"] == "molecule not found by name"


def test_repurposing_scan_live_end_to_end():
    r = repurposing_scan_live("neurodegeneration", top_n=2)
    assert r["validation_source"] == "ChEMBL (live measured bioactivity)"
    assert len(r["candidates_validated"]) >= 1
    assert all("chembl" in c for c in r["candidates_validated"])
