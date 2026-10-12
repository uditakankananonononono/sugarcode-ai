"""Regression tests for two OVERSTATED-repair defects (shard 12). Hermetic."""
from sugarcode.modules.biogpt_lit import extract_claims


def _hit(subject, relation, obj):
    return {"subject": subject, "relation": relation, "object": obj}


def test_two_token_relation_interacts_with_is_extracted():
    assert extract_claims("TP53 interacts with MDM2.") == [_hit("TP53", "binds", "MDM2")]


def test_two_token_relation_associated_with_is_extracted():
    assert extract_claims("APOE associated with Alzheimer.") == [_hit("APOE", "associated_with", "Alzheimer")]


def test_two_token_relation_not_double_counted_with_single_token_rules():
    # "with" and "interacts" alone are not relation words; exactly one triple results
    assert len(extract_claims("BRCA1 interacts with BARD1.")) == 1


def test_two_token_relation_respects_negation_and_loss_rules():
    assert extract_claims("TP53 does not interact with MDM2.") == []
    assert extract_claims("TP53 never interacts with MDM2.") == []
    assert extract_claims("Loss of PTEN interacts with AKT.") == []


def test_two_token_relation_needs_both_neighbors():
    assert extract_claims("TP53 interacts with") == []
    assert extract_claims("interacts with MDM2") == []


def test_single_token_relations_unchanged():
    assert extract_claims("TP53 activates BAX. random words here.") == [_hit("TP53", "activates", "BAX")]
    assert extract_claims("Neither drug inhibits X.") == []


def _fx(monkeypatch, hits):
    from sugarcode.bio import chembl
    monkeypatch.setattr(chembl, "similarity_search", lambda s, cutoff=80, limit=10, offline=False: hits)
    from sugarcode.modules.chemgpt_engine import similarity_check
    return similarity_check("CCO")


def _hit_chembl(cid, name, sim, phase):
    return {"chembl_id": cid, "pref_name": name, "similarity": sim, "max_phase": phase, "smiles": "C"}


def test_phase4_drug_is_approved_neighbor(monkeypatch):
    r = _fx(monkeypatch, [_hit_chembl("CHEMBL25", "ASPIRIN", 100.0, 4)])
    assert [n["chembl_id"] for n in r["approved_neighbors"]] == ["CHEMBL25"]


def test_phase3_only_compound_is_not_approved_neighbor(monkeypatch):
    r = _fx(monkeypatch, [_hit_chembl("CHEMBLX", "INVESTIGATIONAL", 95.0, 3)])
    assert r["approved_neighbors"] == []
    assert r["neighbors"][0]["max_phase"] == 3  # still reported as a neighbor


def test_mixed_neighbors_keep_only_phase4(monkeypatch):
    hits = [_hit_chembl("A", "p3", 99.0, 3), _hit_chembl("B", "p4", 95.0, 4),
            _hit_chembl("C", "p2", 90.0, 2), _hit_chembl("D", "none", 85.0, None),
            _hit_chembl("E", "float4", 84.0, 4.0)]
    r = _fx(monkeypatch, hits)
    assert [n["chembl_id"] for n in r["approved_neighbors"]] == ["B", "E"]
    assert r["closest"]["chembl_id"] == "A"  # closest is similarity-ranked, not approval-ranked


def test_approved_semantics_documented():
    from sugarcode.modules.chemgpt_engine import core
    assert "max_phase" in (core.similarity_check.__doc__ or "") and "4" in core.similarity_check.__doc__
