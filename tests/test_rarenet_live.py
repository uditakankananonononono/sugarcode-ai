import json
import pytest

from sugarcode.bio import entrez
from sugarcode.modules.rarenet_ai import enrich_variants_live, diagnose

ESEARCH = json.dumps({"esearchresult": {"idlist": ["1", "2"]}}).encode()
CLINVAR = json.dumps({"result": {"uids": ["1", "2"], "1": {
    "title": "NM_007294.4(BRCA1):c.68_69del", "germline_classification": {
        "description": "Pathogenic", "review_status": "expert panel"},
    "trait_set": [{"trait_name": "HBOC"}]},
    "2": {"title": "NM_007294.4(BRCA1):c.5266dup", "germline_classification": {
        "description": "Pathogenic", "review_status": "expert panel"},
    "trait_set": [{"trait_name": "HBOC"}]}}}).encode()


@pytest.fixture(autouse=True)
def fake_transport(monkeypatch, tmp_path):
    monkeypatch.setattr(entrez, "CACHE_DIR", tmp_path / "e")
    monkeypatch.setattr(entrez, "_get",
                        lambda path, params, offline=False, retries=3:
                        ESEARCH if "esearch" in path else CLINVAR)


def test_enrich_attaches_live_classification():
    out = enrich_variants_live([{"gene": "BRCA1", "type": "frameshift",
                                 "hgvs": "NM_007294.4:c.68_69del"}])
    cv = out[0]["clinvar"]
    assert cv["status"] == "live"
    assert cv["pathogenic_or_likely"] == 2
    assert cv["exact_match"] and "68_69del" in cv["exact_match"][0]["title"]
    assert "Pathogenic" in cv["interpretation_hint"]


def test_enrich_vus_when_unmatched():
    out = enrich_variants_live([{"gene": "BRCA1", "type": "missense"}])
    assert out[0]["clinvar"]["exact_match"] == []
    assert "VUS" in out[0]["clinvar"]["interpretation_hint"]


def test_enrich_skips_geneless_and_feeds_diagnose():
    vs = enrich_variants_live([{"gene": "BRCA1"}, {"gene": ""}])
    assert vs[1]["clinvar"]["status"].startswith("no gene symbol")
    d = diagnose(symptoms=["fatigue"], variants=vs)
    assert d.get("candidates", d.get("diagnoses"))
