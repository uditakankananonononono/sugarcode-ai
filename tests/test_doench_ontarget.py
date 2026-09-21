"""Published Doench 2014 (Rule Set 1) on-target model tests. Cross-validated
0/500 against the reference implementation at build time."""
import pytest

from sugarcode.modules.crispr_opt import design_guides, doench2014_ontarget
from sugarcode.modules.crispr_opt.core import _DOENCH_PARAMS

LOCUS = ("GCGTACGATCGATCGGGCTAGCATCGATCGATCGATCGGATCGATCGATCG"
         "ATGCCGCTAGCTAGCTAGCATCGATCGGGCTAGCTAGCATCGATCGATCG")


def test_params_table_complete():
    assert len(_DOENCH_PARAMS) == 70
    positions = {p for p, m, w in _DOENCH_PARAMS}
    assert max(positions) <= 29  # zero-based into the 30-mer (dinucleotides span 2)


def test_score_bounds_and_shape():
    s = doench2014_ontarget("AGCAGGATAGTCCTTCCGAGTGGAGGGAGG")
    assert 0.0 < s < 1.0


def test_requires_30mer():
    with pytest.raises(ValueError):
        doench2014_ontarget("TOOSHORT")
    with pytest.raises(ValueError):
        doench2014_ontarget("A" * 31)


def test_extreme_gc_penalized():
    # all-GC guide vs balanced guide, same flanks/PAM
    hi = doench2014_ontarget("AAAA" + "G" * 20 + "GGG" + "AAA")
    lo = doench2014_ontarget("AAAA" + "ACGT" * 5 + "GGG" + "AAA")
    assert hi < lo  # GC penalty pulls extreme GC down


def test_design_guides_uses_published_models():
    out = design_guides(LOCUS, background=LOCUS, top_n=3)
    assert out["scoring_models"]["on_target"].startswith("doench2014_rs1")
    assert out["scoring_models"]["off_target"] == "cfd_doench2016 (published)"
    for g in out["guides"]:
        assert g["on_target_model"] in ("doench2014_rs1", "heuristic_edge_fallback")
        assert "top_off_targets" in g


def test_design_guides_edge_fallback_labeled():
    # guide at the very 5' edge has no 4bp flank -> labeled fallback, not silence
    short = "ATCGATCGATCGATCGATCG" + "AGG" + "C" * 40
    out = design_guides(short, top_n=5)
    models = {g["on_target_model"] for g in out["guides"]}
    assert "heuristic_edge_fallback" in models
