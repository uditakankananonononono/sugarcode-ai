from sugarcode.bio import chembl as C


def test_activities_request_is_globally_ordered(monkeypatch):
    seen = {}
    def fake(url, offline=False):
        seen["url"] = url
        return {"activities": [{"molecule_chembl_id": "M1", "standard_type": "IC50",
                                "standard_value": "0.015", "standard_relation": "=",
                                "pchembl_value": "10.82"}]}
    monkeypatch.setattr(C, "_get", fake)
    out = C.activities_for_target("CHEMBL1862", max_n=5)
    assert "order_by=-pchembl_value" in seen["url"]
    assert "pchembl_value__isnull=false" in seen["url"]
    assert out[0]["value_nM"] == 0.015
