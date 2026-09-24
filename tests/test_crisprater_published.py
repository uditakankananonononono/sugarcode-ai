"""CRISPRater GC window: published model (Labuhn 2018, Fig 4C) uses GC4-13
(10 nt), not 4-14; verified against author-computed scores in the paper's
Supplementary Table 3."""
from sugarcode.modules.crisprater.core import score


def test_gc_window_is_4_to_13():
    # spacer with G at position 14 only differs between windows 4-13 and 4-14
    a = score("AAA" + "G" * 9 + "A" * 8).score   # positions 4-13 all G/C
    b = score("AAA" + "G" * 9 + "A" + "C" + "A" * 6).score  # pos14 = C: would add only to a 4-14 window (G would also hit the G14 base feature)
    import math
    assert math.isclose(a, b, rel_tol=0, abs_tol=1e-12)  # position 14 must not enter the GC feature


def test_published_score_example():
    # Supplementary Table 3 (external screen): author-computed CRISPRater scores
    assert abs(score("GAGTAAGAAGGTTGAACGAA").score - 0.374487835) < 5e-4
    assert abs(score("CCCACATGTTCTCGAGCATA").score - 0.38866522) < 5e-4
    assert abs(score("ACGTACAGAAGCCGATGGAA").score - 0.402842605) < 5e-4
