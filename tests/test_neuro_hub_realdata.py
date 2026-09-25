"""Module 109 neuro_hub: validation against the platform's own registry identities."""
import pytest
from omega.registry import REGISTRY
from omega.search import UnifiedSearch
from sugarcode.modules.neuro_hub import (dashboard, initiate_search,
                                         recent_projects, register_project)
from sugarcode.modules.neuro_hub import core


def _self_retrieval(field):
    e = UnifiedSearch()
    hits = sum(1 for s, sp in REGISTRY.items()
               if e.search(getattr(sp, field), 1)[0]["slug"] == s)
    return hits


def test_bm25_self_retrieval_by_summary_and_name():
    # raw tf*idf (pre-fix) scored 67/95 and 74/95
    assert _self_retrieval("summary") >= 93
    assert _self_retrieval("name") >= 93


def test_name_boost_needs_whole_token():
    e = UnifiedSearch()
    # "of" is a substring of "Off-Target"/"BioFactory" names but not a name token
    r = e.search("design of", 95)
    assert all(x["score"] > 0 for x in r)
    assert e.search("CRISPR guide RNA design off-target", 3)[0]["slug"].startswith("crispr")


def test_search_limit_contract():
    assert initiate_search("protein", 0)["results"] == []
    with pytest.raises(ValueError):
        initiate_search("protein", -1)
    assert len(initiate_search("protein", 3)["results"]) == 3


def test_recent_projects_limit_zero_and_negative(monkeypatch):
    monkeypatch.setattr(core, "_PROJECTS", [])
    for i in range(12):
        register_project(f"p{i}", "neuro_hub")
    assert recent_projects(0) == []
    assert [p["name"] for p in recent_projects(2)] == ["p11", "p10"]
    with pytest.raises(ValueError):
        recent_projects(-1)


def test_register_project_validates_against_registry(monkeypatch):
    monkeypatch.setattr(core, "_PROJECTS", [])
    with pytest.raises(ValueError):
        register_project("x", "not_a_module")
    with pytest.raises(ValueError):
        register_project("  ", "neuro_hub")
    assert register_project(" run1 ", "crispr_opt")["name"] == "run1"


def test_dashboard_matches_registry():
    d = dashboard()
    assert d["compute_flux"]["modules_total"] == len(REGISTRY) == 95
    assert sum(v["total"] for v in d["subnetworks"].values()) == 95
