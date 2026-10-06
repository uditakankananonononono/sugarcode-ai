import pytest
from sugarcode.bio import entrez
from sugarcode.modules.bio_copilot import core as bc
from omega.registry import REGISTRY


def test_literature_route_returns_retrieved_records_not_a_promise(monkeypatch):
    monkeypatch.setattr(entrez, "pubmed_ids", lambda q, retmax=10, offline=False: ["111", "222"])
    monkeypatch.setattr(entrez, "pubmed_abstracts", lambda ids, offline=False: [
        {"pmid": i, "title": f"T{i}", "abstract": "abs " * 200, "year": "2025", "journal": "J"} for i in ids])
    r = bc.answer("what do we know about enhancer silencing")
    assert [p["pmid"] for p in r["papers"]] == ["111", "222"]
    assert r["papers"][0]["url"].endswith("/111/")
    assert len(r["papers"][0]["abstract_excerpt"]) == 400
    assert "no language model" in r["synthesis"]
    assert "in deployment" not in r["answer"]


def test_literature_route_reports_failure_honestly(monkeypatch):
    def boom(*a, **k): raise OSError("no network")
    monkeypatch.setattr(entrez, "pubmed_ids", boom)
    r = bc.literature_route("anything")
    assert r["papers"] == [] and "failed" in r["answer"] and "unreachable" in r["grounding"]


def test_registry_discloses_no_language_model():
    assert "no language model" in REGISTRY["bio_copilot"].summary
