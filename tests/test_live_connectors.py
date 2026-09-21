"""Connector tests are deterministic: transport is monkeypatched with recorded
payloads. Offline mode is exercised explicitly."""
import json
import pytest

from sugarcode.bio import entrez, uniprot
from sugarcode.modules.gene_analysis import live_gene_profile
from sugarcode.modules.openclinvar import live_lookup
from sugarcode.modules.biogpt_lit import KnowledgeGraph, ingest_pubmed, extract_claims
from sugarcode.modules.bio_copilot import live_gene_context

ESEARCH_JSON = json.dumps({"esearchresult": {"idlist": ["7157"]}}).encode()
ESUMMARY_JSON = json.dumps({"result": {"uids": ["7157"], "7157": {
    "name": "TP53", "description": "tumor protein p53", "chromosome": "17",
    "maplocation": "17p13.1", "otheraliases": "P53"}}}).encode()
CLINVAR_JSON = json.dumps({"result": {"uids": ["1", "2"], "1": {
    "title": "NM_007294.4(BRCA1):c.68_69del", "germline_classification": {
        "description": "Pathogenic", "review_status": "reviewed by expert panel"},
    "trait_set": [{"trait_name": "Hereditary breast and ovarian cancer"}]},
    "2": {"title": "NM_007294.4(BRCA1):c.5266dup", "germline_classification": {
        "description": "Uncertain significance", "review_status": "single submitter"},
    "trait_set": [{"trait_name": "Breast cancer"}]}}}).encode()
PUBMED_XML = b"""<PubmedArticleSet><PubmedArticle>
<MedlineCitation><PMID>12345</PMID><Article>
<ArticleTitle>BRCA1 inhibits tumor growth in vivo</ArticleTitle>
<Abstract><AbstractText>BRCA1 inhibits tumor growth. RAD51 activates repair.</AbstractText></Abstract>
<Journal><Title>Nature</Title></Journal>
</Article></MedlineCitation>
<PubmedData><ArticleIdList/></PubmedData></PubmedArticle></PubmedArticleSet>"""
UNIPROT_JSON = json.dumps({"results": [{
    "primaryAccession": "P04637", "uniProtkbId": "P53_HUMAN",
    "proteinDescription": {"recommendedName": {"fullName": {"value": "Cellular tumor antigen p53"}}},
    "organism": {"scientificName": "Homo sapiens"},
    "sequence": {"length": 393, "molWeight": 43653, "value": "MEEPQSDPSV"},
    "features": [{"type": "Domain", "description": "DNA-binding",
                  "location": {"start": {"value": 102}, "end": {"value": 292}}}],
    "uniProtKBCrossReferences": [{"database": "GO", "id": "GO:0003677"}],
    "comments": [{"commentType": "FUNCTION"}]}]}).encode()


CLINVAR_SEARCH_JSON = json.dumps({"esearchresult": {"idlist": ["1", "2"]}}).encode()


def _route(url_or_path, params=None):
    """Map each connector call to its fixture by content inspection."""
    blob = str(url_or_path) + str(params)
    if "pubmed" in blob and "efetch" in blob:
        return PUBMED_XML
    if "clinvar" in blob and "esearch" in blob:
        return CLINVAR_SEARCH_JSON
    if "clinvar" in blob:
        return CLINVAR_JSON
    if "esummary" in blob:
        return ESUMMARY_JSON
    if "uniprot" in blob or str(url_or_path).startswith("http"):
        return UNIPROT_JSON
    return ESEARCH_JSON


@pytest.fixture(autouse=True)
def fake_transport(monkeypatch, tmp_path):
    monkeypatch.setattr(entrez, "CACHE_DIR", tmp_path / "entrez")
    monkeypatch.setattr(uniprot, "CACHE_DIR", tmp_path / "uniprot")
    def fake_entrez(path, params, offline=False, retries=3):
        if offline:
            raise entrez.EntrezError("offline mode: no cache")
        return _route(path, params)

    def fake_uniprot(url, offline=False, retries=3):
        if offline:
            raise uniprot.UniProtError("offline mode: no cache")
        return _route(url)

    monkeypatch.setattr(entrez, "_get", fake_entrez)
    monkeypatch.setattr(uniprot, "_get", fake_uniprot)


def test_entrez_gene_id_and_summary():
    assert entrez.gene_id("TP53") == "7157"
    s = entrez.esummary("gene", ["7157"])
    assert s["7157"]["description"] == "tumor protein p53"


def test_entrez_pubmed_abstracts_parse():
    arts = entrez.pubmed_abstracts(["12345"])
    assert arts[0]["pmid"] == "12345"
    assert "BRCA1" in arts[0]["title"]
    assert arts[0]["journal"] == "Nature"


def test_uniprot_search_normalizes():
    rec = uniprot.search("TP53")
    assert rec["accession"] == "P04637"
    assert rec["length"] == 393
    assert rec["features"][0]["type"] == "Domain"
    assert "GO:0003677" in rec["go_terms"]


def test_offline_mode_without_cache_raises():
    with pytest.raises(entrez.EntrezError):
        entrez.esearch("gene", "never cached", offline=True)


def test_gene_analysis_live_profile_merges_sources():
    p = live_gene_profile("TP53")
    assert p["sources"]["ncbi_gene"]["name"] == "TP53"
    assert p["sources"]["uniprot"]["accession"] == "P04637"
    assert p["protein_stats"]["length"] == 10  # fixture sequence MEEPQSDPSV


def test_openclinvar_live_lookup_counts():
    r = live_lookup("BRCA1")
    assert r["n_variants"] == 2
    assert r["significance_counts"]["Pathogenic"] == 1
    assert r["significance_counts"]["Uncertain significance"] == 1
    assert len(r["pathogenic_or_likely"]) == 1


def test_biogpt_ingest_pubmed_flows_to_graph():
    kg = KnowledgeGraph()
    r = ingest_pubmed(kg, "BRCA1 DNA repair", retmax=1)
    assert r["papers_fetched"] == 1
    assert r["claims_ingested"] >= 1
    q = kg.query("BRCA1", "tumor")
    assert q["consensus"] == "inhibits"


def test_extract_claims_precision():
    claims = extract_claims("BRCA1 inhibits tumor growth. The cells were cultured overnight.")
    assert claims == [{"subject": "BRCA1", "relation": "inhibits", "object": "tumor"}]


def test_copilot_live_context_prefers_uniprot():
    g = live_gene_context("TP53")
    assert g["source"] == "UniProt (live)"
    assert g["protein_name"] == "Cellular tumor antigen p53"
    assert g["domains"][0]["begin"] == 102
