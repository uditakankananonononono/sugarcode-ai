"""Real-behavior validation for neodti_engine (module 108).

BUG 79: predict_interactions kept drugs with NO drug-target-pathway-disease
path and ranked them by the untrained random-embedding cosine alone. For
T2D, myeloma, pulmonary_hypertension, ED, alcoholism, fungal_infection and
GERD the ENTIRE candidate list was zero-path noise (T2D top hit thalidomide
tri 0.338 with zero evidence paths). Candidates are now restricted to drugs
with >=1 mechanistic path (same contract as repurposing_scan); empty lists
carry an explicit status; the 50-diagnostic panel pads rank slots for <5
candidates and guards the top margin at 1 candidate.
"""
import pytest
from sugarcode.modules.neodti_engine import core as nd

NOISE_DISEASES = ["T2D", "myeloma", "pulmonary_hypertension", "ED",
                  "alcoholism", "fungal_infection", "GERD"]


def test_every_candidate_has_a_mechanistic_path():
    for d in ["arthritis", "cancer_solid", "neurodegeneration", "aging",
              "cardiovascular", "cancer_inflammatory", "basal_cell_carcinoma"]:
        r = nd.predict_interactions(d, top_n=10)
        assert r["candidates"], d
        assert all(c["path_count"] > 0 for c in r["candidates"]), d
        assert r["excluded_zero_path_drugs"] >= 0


def test_noise_diseases_report_status_not_candidates():
    for d in NOISE_DISEASES:
        r = nd.predict_interactions(d, top_n=10)
        assert r["candidates"] == [], d
        assert "extend the graph" in r["status"], d
        a = nd.analyze_repurposing(d)
        assert a["diagnostic_count"] == 0 and a["diagnostics"] == {}, d


def test_scan_consistency_arthritis():
    r = nd.repurposing_scan("arthritis")
    assert [c["drug"] for c in r["candidates"]] == ["aspirin", "thalidomide"]
    top = r["candidates"][0]
    assert top["n_paths"] == 2
    # tri = .45*min(1,.4*2) + .25*min(2/3,1) + .3*1
    assert top["therapeutic_resilience_index"] == round(.45 * .8 + .25 * (2 / 3) + .3, 3)


def test_diagnostics_fifty_for_short_candidate_lists():
    assert nd.analyze_repurposing("cardiovascular")["diagnostic_count"] == 50  # 1 candidate
    assert nd.analyze_repurposing("aging")["diagnostic_count"] == 50          # 2 candidates
    a = nd.analyze_repurposing("aging")
    assert a["diagnostics"]["rank_3_tri"] is None


def test_graph_and_embeddings_shapes():
    g = nd.build_multiplex_graph()
    assert g["layer_counts"]["drug"] == len(nd.DRUG_TARGETS)
    e = nd.graph_neural_embeddings(g, dimensions=8, layers=2)
    assert len(e["embeddings"]) == g["node_count"]
    assert e["dimensions"] == 8
