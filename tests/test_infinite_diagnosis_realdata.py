"""Real-case validation for infinite_diagnosis (module 102).

Defects found on real clinical phrasings (sweep 102):
1. function words ("and", "with") drove the catalog ranker, so
   "tall stature and lens dislocation" returned SynDroid/Micro-Tx/... angles
   that came only from the word "and";
2. module specs never name diseases/symptoms/genes, so "cystic fibrosis" or
   "CFTR" matched zero modules although RareNet AI holds curated records.
Live checks (recorded in mega27-01 benchmarks/sweep_infinite_diagnosis.json):
ClinVar VCV000007105 CFTR p.Phe508del (Pathogenic, practice guideline) is the
lead hypothesis; VCV000015333 HBB p.Glu7Val (Pathogenic, 2-star) is scored but
not a lead because HBB is outside the CF symptom differential.
"""
from sugarcode.modules.infinite_diagnosis import cross_domain_diagnosis
from sugarcode.modules.infinite_diagnosis.core import (
    _content_query, _curated_disease_matches,
)
from omega.search import UnifiedSearch


def _angles(case):
    r = cross_domain_diagnosis(case, limit=4, offline=True)
    return r, {m for c in r["hidden_clusters"] for m in c["relevant_modules"]}


def test_function_words_alone_rank_modules_in_raw_search():
    # documents the upstream behaviour the fix works around
    assert UnifiedSearch().search("and", 5)


def test_content_query_drops_function_words():
    assert _content_query("Tall stature AND lens dislocation, with myopia") == \
        "tall stature lens dislocation myopia"


def test_function_word_only_case_has_no_angles():
    r, mods = _angles("and with the")
    assert mods == set()
    assert r["catalog_status"] == "no module in the catalog matched the case terms"


def test_marfan_phrasing_routes_to_rarenet_only():
    r, mods = _angles("tall stature and lens dislocation")
    assert mods == {"RareNet AI"}
    assert r["curated_disease_matches"][0]["disease"] == "marfan"
    assert set(r["curated_disease_matches"][0]["matched_via"]) == {
        "symptom:lens_dislocation", "symptom:tall_stature"}


def test_disease_name_and_gene_symbol_bridge():
    for case, disease in [("cystic fibrosis sweat chloride", "cystic_fibrosis"),
                          ("CFTR", "cystic_fibrosis"),
                          ("child with seizures and musty odor", "phenylketonuria"),
                          ("duchenne md", "duchenne_md")]:
        r, mods = _angles(case)
        assert "RareNet AI" in mods, case
        assert [m["disease"] for m in r["curated_disease_matches"]] == [disease], case


def test_gene_symbol_is_whole_word():
    assert _curated_disease_matches("dmdx mouse") == []
    assert _curated_disease_matches("pahs") == []


def test_unrelated_case_keeps_topic_angles_and_no_curated_match():
    r, mods = _angles("patient with microbiome dysbiosis and phage therapy")
    assert {"Micro-Tx", "Phage-Tx"} <= mods
    assert r["curated_disease_matches"] == []
    assert "RareNet AI" not in mods


def test_roadmap_uses_rarenet_angle():
    r, _ = _angles("cystic fibrosis")
    assert r["experimental_roadmap"][0]["modules"] == ["RareNet AI"]
    assert r["experimental_roadmap"][-1]["angle"] == "synthesis"
