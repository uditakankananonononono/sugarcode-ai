"""Regression tests for the gene_analysis audit defects (offline fakes; no network)."""
import ast
import json
from datetime import datetime
from pathlib import Path

import pytest

import sugarcode.modules.gene_analysis.core as core
from sugarcode.bio import entrez, reactome, uniprot
from sugarcode.modules import openclinvar
from sugarcode.modules.gene_analysis import gene_profile, live_gene_profile, live_pathways, live_publication_trend

REACTOME = [{"displayName": "DNA Damage/Telomere Stress Induced Senescence", "stId": "R-HSA-2559586", "isInDisease": False}]


@pytest.fixture
def fakes(monkeypatch, tmp_path):
    monkeypatch.setattr(reactome, "CACHE_DIR", tmp_path / "r")
    calls = []

    def fake_reactome(path, params, offline=False, retries=3):
        calls.append(path)
        return json.dumps(REACTOME).encode() if "Q13315" in path else None

    monkeypatch.setattr(reactome, "_get", fake_reactome)
    monkeypatch.setattr(uniprot, "search", lambda symbol, organism_id=9606, offline=False:
                        {"accession": {"ATM": "Q13315"}.get(symbol, "P00000"), "sequence": "MSLVLNDLLI"})
    monkeypatch.setattr(entrez, "gene_id", lambda *a, **k: None)
    monkeypatch.setattr(entrez, "clinvar_variants", lambda gene, retmax=20, offline=False: [
        {"uid": "1", "title": "x", "significance": "Pathogenic", "review_status": "", "condition": ""},
        {"uid": "2", "title": "y", "significance": "Benign", "review_status": "", "condition": ""}])
    return calls


def test_pathways_come_from_reactome_for_any_gene(fakes):
    pathways = live_pathways("ATM")
    assert pathways[0]["id"] == "R-HSA-2559586" and pathways[0]["source"] == "Reactome (live)"
    assert core._pathway_links("ATM") == []  # the old built-in table had nothing for ATM
    assert live_pathways("NOTAGENE") == []  # Reactome 404 -> honest empty list


def test_pathway_lookup_failure_falls_back_and_says_so(monkeypatch, fakes):
    def boom(*a, **k):
        raise reactome.ReactomeError("down")
    monkeypatch.setattr(reactome, "_get", boom)
    fallback = live_pathways("TP53")
    assert fallback and all("live lookup failed" in p["source"] for p in fallback)


def test_live_profile_includes_clinvar_and_reactome(fakes):
    profile = live_gene_profile("ATM")
    assert profile["sources"]["clinvar"]["significance_counts"] == {"Pathogenic": 1, "Benign": 1}
    assert profile["sources"]["reactome"]["pathways"][0]["id"] == "R-HSA-2559586"


def test_gene_profile_live_queries_clinvar_per_variant(monkeypatch, fakes):
    seen = []

    def fake_live(gene, variant, offline=False, **kwargs):
        seen.append((gene, variant))
        return {"gene": gene, "variant": variant, "classification": "pathogenic", "evidence": [{"rule": "CLINVAR_LIVE"}]}

    monkeypatch.setattr(openclinvar.core, "interpret_variant_live", fake_live)
    seq = "ATG" + "GCT" * 60 + "TAA"
    live = gene_profile("ATM", seq, variants=[{"variant": "c.68_69del", "consequence": "frameshift"}], live=True)
    assert seen == [("ATM", "c.68_69del")] and live["variants"][0]["source"] == "ClinVar (live) + rules"
    assert live["pathway_links"][0]["source"] == "Reactome (live)"
    offline = gene_profile("ATM", seq, variants=[{"variant": "c.68_69del", "consequence": "frameshift"}])
    assert offline["variants"][0]["source"] == "offline rules" and len(seen) == 1

    def down(*a, **k):
        raise entrez.EntrezError("down")
    monkeypatch.setattr(openclinvar.core, "interpret_variant_live", down)
    failed = gene_profile("ATM", seq, variants=[{"variant": "c.68_69del", "consequence": "frameshift"}], live=True)
    assert "ClinVar lookup failed" in failed["variants"][0]["source"]


def test_trend_ignores_the_partial_current_year(monkeypatch, tmp_path):
    now = datetime.now().year
    counts = {now - 3: 100, now - 2: 110, now - 1: 150, now: 40}  # current year only part-way

    def fake_get(path, params, offline=False, retries=3):
        year = int(params["term"].split(" AND ")[1][:4])
        return json.dumps({"esearchresult": {"count": str(counts.get(year, 0)), "idlist": []}}).encode()

    monkeypatch.setattr(entrez, "_get", fake_get)
    trend = live_publication_trend("BRCA1", years=3)
    assert list(trend["counts_by_year"]) == [now - 3, now - 2, now - 1]
    assert trend["trend"] == "rising"  # the old code compared 40 (partial) with 100 and said "falling"
    assert trend["partial_current_year"] == {"year": now, "count_so_far": 40}


def test_no_function_is_defined_twice():
    tree = ast.parse(Path(core.__file__).read_text())
    names = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
    assert len(names) == len(set(names))
