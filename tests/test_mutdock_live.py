import json
import pytest

from sugarcode.bio import uniprot
from sugarcode.modules.mutdock import live_mutation_context

UNIPROT = json.dumps({"results": [{
    "primaryAccession": "P04637", "uniProtkbId": "P53_HUMAN",
    "proteinDescription": {"recommendedName": {"fullName": {"value": "p53"}}},
    "organism": {"scientificName": "Homo sapiens"},
    "sequence": {"length": 21, "molWeight": 2400,
                 "value": "MKRQEHLMPSDPRTGHFRRRV"},
    "features": [{"type": "Binding site", "description": "DNA contact",
                  "location": {"start": {"value": 13}, "end": {"value": 13}}}],
    "uniProtKBCrossReferences": [], "comments": []}]}).encode()


@pytest.fixture(autouse=True)
def fake_transport(monkeypatch, tmp_path):
    monkeypatch.setattr(uniprot, "CACHE_DIR", tmp_path / "u")
    monkeypatch.setattr(uniprot, "_get", lambda url, offline=False, retries=3: UNIPROT)


def test_live_context_numbering_and_features():
    # fixture seq: M K R Q E H L M P S D P R T G H F R R R V (21 aa)
    # position 13 = R, annotated Binding site
    r = live_mutation_context("TP53", 13, "A", "CCO")
    assert r["source"] == "UniProt (live)"
    assert r["wt_residue"] == "R"
    assert r["mutation"] == "R13A"          # 1-based numbering preserved exactly
    assert r["in_functional_site"]
    assert r["functional_features_at_position"][0]["type"] == "Binding site"
    assert "window" in r and len(r["window"]["sequence"]) <= 21


def test_live_context_out_of_range():
    with pytest.raises(ValueError):
        live_mutation_context("TP53", 99, "A", "CCO")


def test_live_context_no_feature_position():
    r = live_mutation_context("TP53", 2, "G", "CCO")
    assert not r["in_functional_site"]
    assert "screening-level" in r["interpretation"]
