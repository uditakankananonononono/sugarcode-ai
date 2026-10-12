"""phenotype_match score stays within [0, 1]."""
from sugarcode.modules.openclinvar.core import phenotype_match


def test_score_with_exact_and_ancestor_partial_does_not_exceed_one():
    m = phenotype_match(["HP:a", "HP:b"], ["HP:a", "HP:b"], {"HP:a": ("HP:b",)})
    assert m["exact_matches"] == 2
    assert m["semantic_partial"] == 1.0  # raw ratio is (2+1)/2 = 1.5
    assert m["score"] == 1.0


def test_many_ancestor_pairs_do_not_exceed_one():
    anc = {"HP:a": ("HP:b", "HP:c", "HP:d")}
    m = phenotype_match(["HP:a", "HP:b"], ["HP:b", "HP:c", "HP:d"], anc)
    assert 0.0 <= m["score"] <= 1.0


def test_scores_below_one_are_unchanged():
    assert phenotype_match(["HP:a"], ["HP:b"], {"HP:a": ("HP:b",)})["score"] == 0.25
    assert phenotype_match(["HP:a", "HP:b"], ["HP:a", "HP:c"])["score"] == 1 / 3
    assert phenotype_match(["HP:a"], ["HP:a"])["score"] == 1.0
    assert phenotype_match([], [])["score"] == 0.0
