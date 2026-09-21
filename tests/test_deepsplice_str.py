from sugarcode.modules.deepsplice import score_donor, variant_effect
from sugarcode.modules.str_scope import find_strs, expansion_call, diagnostic_index


def test_consensus_donor_scores_high():
    assert score_donor("AAGGTAAGT") > 0.8


def test_variant_disrupts_donor():
    r = variant_effect("AAGGTAAGT", "AACTTAAGT", "donor")
    assert r["delta"] < 0
    assert "exon" in r["consequence"] or "splicing" in r["consequence"]


def test_find_strs():
    hits = find_strs("AAA" + "CAG" * 12 + "TTT", min_repeats=4)
    assert hits and hits[0]["unit"] == "CAG" and hits[0]["repeats"] == 12


def test_expansion_and_index():
    c = expansion_call(45, 20, "CAG")
    assert "expanded" in c["classification"]
    d = diagnostic_index([{"unit": "CAG", "delta": 25}], repair_pathway_links=2)
    assert d["diagnostic_potential_index"] > 0.3
