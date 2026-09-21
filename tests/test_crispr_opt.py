from sugarcode.modules.crispr_opt import (design_guides, pam_sites,
                                          score_on_target, score_off_targets)

LOCUS = ("GCGTACGATCGATCGGGCTAGCATCGATCGATCGATCGGATCGATCGATCG"
         "ATGCCGCTAGCTAGCTAGCATCGATCGGGCTAGCTAGCATCGATCGATCG")


def test_pam_sites_found():
    sites = pam_sites(LOCUS, "NGG")
    assert len(sites) >= 1
    assert all(s["pam"][1:] == "GG" for s in sites)


def test_on_target_bounds():
    s = score_on_target("ATCGATCGATCGATCGATCG")
    assert 0.0 <= s <= 1.0


def test_off_targets_seed_weighting():
    bg = "TTT" + "ATCGATCGATCGATCGATCA" + "GGG"  # 1 mismatch at 3' end (seed)
    hits = score_off_targets("ATCGATCGATCGATCGATCG", bg, max_mismatches=3)
    assert any(h["mismatches"] == 1 and h["risk"] > 0.2 for h in hits)


def test_design_guides_ranked():
    out = design_guides(LOCUS, background=LOCUS, top_n=3)
    assert out["candidates"] >= 1
    comps = [g["composite"] for g in out["guides"]]
    assert comps == sorted(comps, reverse=True)
    assert "browser_track" in out and out["browser_track"]["tracks"]
