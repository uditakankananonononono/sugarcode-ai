"""Regression test for BUG 63: compare_profiles/nearest_mechanism computed cosine
similarity over raw signature vectors (~1.0 in every dimension), so the constant
baseline dominated and mechanistically distinct mechanisms scored ~0.999 -
novel_mechanism_hint could never fire. Similarity is now over baseline-subtracted deltas."""
from sugarcode.modules import cellpainter as cp


def _profiles():
    return [cp.profile_perturbation(m, 1.0, 24.0)
            for m in ["dna_damage", "mitochondrial_toxin", "microtubule_poison"]]


def test_distinct_mechanisms_are_not_identical():
    comp = cp.compare_profiles(_profiles())
    dna_vs_mito = [s for s in comp["similarities"]
                   if set(s["pair"]) == {"dna_damage", "mitochondrial_toxin"}][0]
    assert dna_vs_mito["cosine_similarity"] < 0.5  # was 0.9988
    assert comp["novel_mechanism_hint"] != "all profiles similar"


def test_same_mechanism_still_similar():
    a = cp.profile_perturbation("dna_damage", 1.0, 24.0)
    b = cp.profile_perturbation("dna_damage", 2.0, 24.0)
    comp = cp.compare_profiles([a, b])
    assert comp["similarities"][0]["cosine_similarity"] > 0.99


def test_nearest_mechanism_self_match_wins():
    ps = _profiles()
    matches = cp.nearest_mechanism(ps[0], ps[1:])
    assert matches[0]["similarity"] < 0.5  # orthogonal mechanisms score low
    self_match = cp.nearest_mechanism(ps[0], [cp.profile_perturbation("dna_damage", 1.5, 24.0)])
    assert self_match[0]["similarity"] > 0.99
