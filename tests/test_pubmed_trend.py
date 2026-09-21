import json
import pytest

from sugarcode.bio import entrez
from sugarcode.modules.gene_analysis import live_publication_trend


@pytest.fixture(autouse=True)
def fake_transport(monkeypatch, tmp_path):
    monkeypatch.setattr(entrez, "CACHE_DIR", tmp_path / "e")
    counts = {"2024": "100", "2025": "130", "2026": "160"}

    def fake_get(path, params, offline=False, retries=3):
        if offline:
            raise entrez.EntrezError("offline")
        year = params["term"].split(" AND ")[1][:4]
        return json.dumps({"esearchresult": {"count": counts.get(year, "0"),
                                             "idlist": []}}).encode()

    monkeypatch.setattr(entrez, "_get", fake_get)


def test_trend_counts_and_direction():
    t = live_publication_trend("BRCA1", years=3)
    assert t["source"] == "PubMed (live)"
    vals = list(t["counts_by_year"].values())
    assert vals == sorted(vals)  # rising fixture
    assert t["trend"] == "rising"
