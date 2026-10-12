"""Regression test for behavior at base revision 99cb2d32."""
import io
import json

from sugarcode.modules.qsar_bench.chembl_client import ChEMBLQSARClient


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def test_chembl_standard_type_is_filtered_client_side(tmp_path, monkeypatch):
    acts = [
        {"molecule_chembl_id": "M1", "standard_relation": "=", "pchembl_value": "7.0", "standard_type": "IC50", "document_year": 2019},
        {"molecule_chembl_id": "M1", "standard_relation": "=", "pchembl_value": "7.4", "standard_type": "Ki", "document_year": 2021},
        # server returned a type that was not requested: old code kept it (pChEMBL 5.0)
        {"molecule_chembl_id": "M2", "standard_relation": "=", "pchembl_value": "5.0", "standard_type": "EC50", "document_year": 2018},
        {"molecule_chembl_id": "M2", "standard_relation": "=", "pchembl_value": "5.1", "document_year": 2018},
    ]
    mols = [{"molecule_chembl_id": "M1", "molecule_structures": {"canonical_smiles": "CCO"}},
            {"molecule_chembl_id": "M2", "molecule_structures": {"canonical_smiles": "CCC"}}]

    def fake(req, timeout=0):
        body = {"activities": acts} if "activity.json" in req.full_url else {"molecules": mols}
        return _Resp(json.dumps(body).encode())

    monkeypatch.setattr("urllib.request.urlopen", fake)
    r = ChEMBLQSARClient(tmp_path, min_interval=0).target_dataset("CHEMBL1")
    assert [x["smiles"] for x in r["records"]] == ["CCO"]
    assert r["records"][0]["replicate_count"] == 2
    assert r["excluded"]["non_requested_type"] == 2
    # a caller that requests EC50 gets it
    r2 = ChEMBLQSARClient(tmp_path / "b", min_interval=0).target_dataset("CHEMBL1", standard_types=("EC50",))
    assert [x["smiles"] for x in r2["records"]] == ["CCC"]
