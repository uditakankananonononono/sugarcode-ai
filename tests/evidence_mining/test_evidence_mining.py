import json
from pathlib import Path
import pytest
from sugarcode.modules.evidence_mining import (CachedHTTPClient, ClinicalTrialsClient,
    EvidenceRecord, OfflineCacheMiss, PubMedClient, build_evidence_table, extract_text_evidence)


def test_cache_sha_offline_and_corruption(tmp_path):
    calls = []
    def transport(url, headers, timeout):
        calls.append(url); return b'{"ok": true}'
    c = CachedHTTPClient(tmp_path, min_interval=0, transport=transport)
    assert c.json("https://example.test/x", {"b": 2, "a": 1}) == {"ok": True}
    assert c.json("https://example.test/x", {"a": 1, "b": 2}, offline=True) == {"ok": True}
    assert len(calls) == 1
    next(tmp_path.glob("*.body")).write_bytes(b"tampered")
    with pytest.raises(OfflineCacheMiss):
        c.get("https://example.test/x", {"a": 1, "b": 2}, offline=True)


def test_offline_miss_never_calls_transport(tmp_path):
    def fail(*args): raise AssertionError("network called")
    with pytest.raises(OfflineCacheMiss):
        CachedHTTPClient(tmp_path, transport=fail).get("https://example.test", offline=True)


def test_pubmed_esearch_efetch_and_extraction(tmp_path):
    xml = b'''<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID><Article>
    <ArticleTitle>Therapy trial</ArticleTitle><Abstract><AbstractText>We randomized n=120 patients. The primary endpoint was overall survival. Survival significantly improved.</AbstractText></Abstract>
    <PublicationTypeList><PublicationType>Randomized Controlled Trial</PublicationType></PublicationTypeList></Article></MedlineCitation>
    <PubmedData><ArticleIdList><ArticleId IdType="doi">10.1/test</ArticleId></ArticleIdList></PubmedData></PubmedArticle></PubmedArticleSet>'''
    def transport(url, headers, timeout):
        return json.dumps({"esearchresult": {"idlist": ["123"]}}).encode() if "esearch" in url else xml
    http = CachedHTTPClient(tmp_path, min_interval=0, transport=transport)
    rows = PubMedClient(tmp_path, http=http).query("therapy")
    assert rows[0].source_id == "123" and rows[0].sample_size == 120
    assert rows[0].endpoints == ["overall survival"]
    assert rows[0].effect_direction == "stated_effect" and rows[0].doi == "10.1/test"


def test_trials_v2_mapping(tmp_path):
    payload = {"studies": [{"protocolSection": {
      "identificationModule": {"nctId": "NCT00000001", "briefTitle": "A study"},
      "statusModule": {"overallStatus": "COMPLETED", "studyFirstPostDateStruct": {"date": "2024-01-02"}},
      "designModule": {"studyType": "INTERVENTIONAL", "enrollmentInfo": {"count": 42}},
      "armsInterventionsModule": {"interventions": [{"name": "Drug A"}]},
      "outcomesModule": {"primaryOutcomes": [{"measure": "Overall survival"}]}}}]}
    http = CachedHTTPClient(tmp_path, min_interval=0, transport=lambda *_: json.dumps(payload).encode())
    row = ClinicalTrialsClient(tmp_path, http=http).search("cancer")[0]
    assert row.sample_size == 42 and row.endpoints == ["primary: Overall survival"]
    assert row.url.endswith("NCT00000001") and row.effect_direction == "Missing"


def test_extraction_does_not_invent_and_table_deduplicates():
    assert extract_text_evidence("An exploratory laboratory study.")["sample_size"] == "Missing"
    a = EvidenceRecord("PubMed", "1", "Same title", "u")
    b = EvidenceRecord("PubMed", "1", "Different title", "v")
    table = build_evidence_table([a, b])
    assert len(table) == 1 and "raw" not in table[0]



def test_trials_result_values_and_population_are_verbatim(tmp_path):
    study = {
        "protocolSection": {
            "identificationModule": {"nctId": "NCT00000002", "briefTitle": "Result study"},
            "statusModule": {}, "designModule": {},
            "eligibilityModule": {"sex": "ALL", "minimumAge": "18 Years", "maximumAge": "65 Years", "healthyVolunteers": False},
            "outcomesModule": {"primaryOutcomes": [{"measure": "Pain score", "timeFrame": "Week 12"}]},
        },
        "resultsSection": {"outcomeMeasuresModule": {"outcomeMeasures": [
            {"title": "Pain score", "analyses": [{"paramType": "MEAN_DIFFERENCE", "paramValue": "-1.2", "pValue": "0.03", "statisticalMethod": "t-test"}]}
        ]}},
    }
    http = CachedHTTPClient(tmp_path, min_interval=0, transport=lambda *_: json.dumps({"studies": [study]}).encode())
    row = ClinicalTrialsClient(tmp_path, http=http).search("pain")[0]
    assert row.population == "ALL; 18 Years to 65 Years; healthy volunteers: false"
    assert row.endpoints == ["primary: Pain score (Week 12)"]
    assert "MEAN_DIFFERENCE; -1.2; p=0.03" in row.effect_text
    assert row.effect_direction == "reported_not_inferred"
