"""Regression tests for BUG 51 (phageforge off-target screen mislabeled and
perfect-match off-targets silently skipped) and BUG 52 (vacuous
cocktail coverage fraction without a target panel)."""
from sugarcode.modules.phageforge import core as PF
from sugarcode.modules.crispr_opt import design_guides, score_off_targets_cfd

G = "AGCGCAGCTTGTCGGCCATG"  # real top guide from blaNDM-1 (FN396876)


def test_perfect_match_offtarget_reported():
    bg = "T" * 40 + G + "AGG" + "C" * 40
    hits = score_off_targets_cfd(G, bg)
    perfect = [h for h in hits if h["mismatches"] == 0]
    assert perfect and perfect[0]["cfd_score"] == 1.0 and perfect[0]["risk"] == "high"


def test_exclude_sites_skips_own_locus():
    bg = "T" * 40 + G + "AGG" + "C" * 40
    hits = score_off_targets_cfd(G, bg, exclude_sites={(40, "+")})
    assert all(h["mismatches"] > 0 for h in hits)


def test_design_guides_self_excluded_but_duplicate_reported():
    unit = G + "AGG"
    seq = "TT" * 10 + unit + "CC" * 10 + unit + "TT" * 10
    out = design_guides(seq, background=seq, top_n=50)
    cand = [c for c in out["guides"] if c["guide"] == G]
    assert cand, "guide not among candidates"
    for c in cand:
        perfect = [h for h in c["top_off_targets"] if h["mismatches"] == 0]
        assert perfect, "the second copy must be reported as a perfect-match hit"
        own = (c["start"], "+") if c["strand"] == "+" else None
        for h in perfect:
            assert (h["position"], h["strand"]) != own


def test_design_guides_distinct_background_reports_perfect_match():
    seq = "TT" * 10 + G + "AGG" + "CC" * 30
    bg = "A" * 50 + G + "AGG" + "GG" * 25
    out = design_guides(seq, background=bg, top_n=50)
    cand = [c for c in out["guides"] if c["guide"] == G]
    assert cand and any(h["mismatches"] == 0 for h in cand[0]["top_off_targets"])
    assert cand[0]["off_target_risk"] >= 1.0


def test_design_phage_background_text_and_default_unchanged():
    cds = "ATG" + "GCT" * 80 + "TAA"
    out = PF.design_phage(cds, background_genome="ACGT" * 500)
    assert "supplied background genome" in out["specificity"]["off_target_assessment"]
    assert out["specificity"]["background_screened"] == "supplied background genome"
    out2 = PF.design_phage(cds)
    assert "target gene itself" in out2["specificity"]["off_target_assessment"]
    assert out2["specificity"]["background_screened"] == "target gene only"
    assert out2["backbone"] == "P1" and out2["payload"]["fits"]


def test_cocktail_coverage_target_hosts():
    r = PF.cocktail_coverage({"p1": ["a", "b"], "p2": ["b"]}, target_hosts=["a", "b", "c"])
    assert r["coverage_fraction"] == 2 / 3 and r["uncovered_targets"] == ["c"]
    legacy = PF.cocktail_coverage({"p1": ["a", "b"], "p2": ["b"]})
    assert legacy["coverage_fraction"] == 1.0
