import pytest
from sugarcode.modules.infinite_diagnosis import *

CASE_TEXT = "chronic cough with salty skin and poor growth"


def _joint_result():
 return joint_case_view(["chronic cough", "salty skin", "poor growth"], [{"gene": "CFTR", "hgvs": "c.1521_1523delCTT"}], offline=True)


def test_cross_domain_top_level_keys():
 r = cross_domain_diagnosis(CASE_TEXT)
 assert set(r.keys()) == {"biomarker_candidates", "case", "catalog_status", "curated_disease_matches", "experimental_roadmap", "hidden_clusters", "novelty_note"}
 assert isinstance(r["case"], str)
 assert isinstance(r["novelty_note"], str)
 assert isinstance(r["biomarker_candidates"], list)
 assert all(isinstance(item, str) for item in r["biomarker_candidates"])


def test_hidden_clusters_shape():
 r = cross_domain_diagnosis(CASE_TEXT)
 clusters = r["hidden_clusters"]
 assert isinstance(clusters, list) and len(clusters) > 0
 for item in clusters:
  assert set(item.keys()) == {"angle", "diagnostic_hook", "relevant_modules"}
  assert isinstance(item["angle"], str)
  assert isinstance(item["diagnostic_hook"], str)
  assert isinstance(item["relevant_modules"], list)
  assert all(isinstance(mod, str) for mod in item["relevant_modules"])


def test_roadmap_phases_and_synthesis():
 r = cross_domain_diagnosis(CASE_TEXT)
 roadmap = r["experimental_roadmap"]
 assert isinstance(roadmap, list) and len(roadmap) > 0
 for idx, step in enumerate(roadmap):
  assert set(step.keys()) == {"phase", "angle", "action", "modules"}
  assert step["phase"] == idx + 1
  assert isinstance(step["angle"], str)
  assert isinstance(step["action"], str)
  assert all(isinstance(mod, str) for mod in step["modules"])
 assert roadmap[-1]["angle"] == "synthesis"


def test_joint_top_level_keys():
 r = _joint_result()
 assert set(r.keys()) == {"disclaimer", "limits", "symptom_differential", "top_hypothesis", "variant_panel_summary"}
 assert isinstance(r["disclaimer"], str)
 assert isinstance(r["limits"], list) and len(r["limits"]) == 2
 assert all(isinstance(item, str) for item in r["limits"])
 assert isinstance(r["symptom_differential"], list)
 assert all(isinstance(item, dict) for item in r["symptom_differential"])


def test_variant_panel_shape():
 panel = _joint_result()["variant_panel_summary"]
 assert isinstance(panel, list) and len(panel) > 0
 for item in panel:
  assert set(item.keys()) == {"gene", "hgvs", "support_score", "evidence_class", "gene_named_in_symptom_differential", "lead_hypothesis"}
  assert isinstance(item["gene"], str)
  assert isinstance(item["hgvs"], str)
  assert isinstance(item["support_score"], (int, float))
  assert isinstance(item["evidence_class"], str)
  assert isinstance(item["gene_named_in_symptom_differential"], bool)
  assert isinstance(item["lead_hypothesis"], bool)


def test_top_hypothesis_matches_lead():
 r = _joint_result()
 panel = r["variant_panel_summary"]
 lead = next((item for item in panel if item["lead_hypothesis"]), None)
 assert r["top_hypothesis"] == lead


# --- hermetic literature + joint-view fixtures (no live NCBI in CI) ---
from sugarcode.modules.infinite_diagnosis import core as _core
from sugarcode.bio.entrez import EntrezError

_RECS = [{"pmid": "11111111", "year": "2024", "title": "Sweat chloride as a diagnostic biomarker", "abstract": "", "journal": "J"}]


@pytest.fixture(autouse=True)
def _no_live_pubmed(monkeypatch):
 monkeypatch.setattr(_core, "pubmed_ids", lambda q, retmax=10, offline=False: ["11111111"])
 monkeypatch.setattr(_core, "pubmed_abstracts", lambda ids, offline=False: list(_RECS))


def test_literature_hits_become_biomarker_candidates():
 r = cross_domain_diagnosis(CASE_TEXT)
 assert r["biomarker_candidates"] == ["PMID 11111111 (2024): Sweat chloride as a diagnostic biomarker"]
 assert "1 PubMed records" in r["novelty_note"]


def test_literature_no_hits_is_not_a_failure(monkeypatch):
 calls = []
 monkeypatch.setattr(_core, "pubmed_ids", lambda q, retmax=10, offline=False: [])
 monkeypatch.setattr(_core, "pubmed_abstracts", lambda ids, offline=False: calls.append(ids) or [])
 r = cross_domain_diagnosis(CASE_TEXT)
 assert r["biomarker_candidates"] == [] and calls == []
 assert "no records" in r["novelty_note"] and "failed" not in r["novelty_note"]


def test_literature_failure_is_reported(monkeypatch):
 def boom(q, retmax=10, offline=False):
  raise EntrezError("network down")
 monkeypatch.setattr(_core, "pubmed_ids", boom)
 r = cross_domain_diagnosis(CASE_TEXT)
 assert r["biomarker_candidates"] == []
 assert "lookup failed" in r["novelty_note"]


def test_joint_failed_lookups_marked_not_assessed(monkeypatch):
 from sugarcode.modules.rarenet_ai import core as rn
 panel = {"panel": [{"gene": "CFTR", "hgvs": "c.1521_1523del",
   "clinvar": {"status": "lookup failed: EntrezError: offline"},
   "gnomad": {"status": "lookup failed: GnomADError: offline"},
   "gene_constraint": {"status": "ok"},
   "support_score": 0.0, "score_components": [], "evidence_class": "little/no support"}],
  "disclaimer": "d"}
 monkeypatch.setattr(rn, "variant_evidence_panel", lambda v, offline=False: panel)
 row = _joint_result()["variant_panel_summary"][0]
 assert row["evidence_class"] == "not assessed - lookups failed: clinvar, gnomad"
 assert row["support_score"] == 0.0 and row["lead_hypothesis"] is False
