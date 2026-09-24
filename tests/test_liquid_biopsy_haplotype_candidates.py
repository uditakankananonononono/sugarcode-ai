"""Regression (BUG 45): partial fragments must be able to recover an unseen full haplotype."""
from sugarcode.modules.liquid_biopsy.core import bayesian_haplotype_inference


def test_partial_fragments_recover_full_haplotype():
    frags = [[1, 1, -1]] * 30 + [[-1, 1, 1]] * 30 + [[0, 0, -1]] * 30 + [[-1, 0, 0]] * 30
    top = bayesian_haplotype_inference(frags)["haplotypes"][:2]
    assert {h["haplotype"] for h in top} == {"111", "000"}
    assert all(h["posterior_mean"] > 0.4 for h in top)


def test_many_loci_uses_pairwise_merges():
    a = [1, 0] * 7  # 14 loci > exhaustive limit
    left = a[:8] + [-1] * 6
    right = [-1] * 6 + a[6:]
    top = bayesian_haplotype_inference([left] * 20 + [right] * 20)["haplotypes"][0]
    assert top["haplotype"] == "".join(map(str, a))
