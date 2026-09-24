"""Regression tests: IUPAC-aware reverse complement for degenerate sites, and linear-end cuts (found vs Biopython on pBR322/lambda)."""
from sugarcode.bio import restriction as rs


def test_iupac_revcomp():
    assert rs.revcomp("GTMKAC") == "GTMKAC"
    assert rs.revcomp("GGYRCC") == "GGYRCC"
    assert rs.revcomp("RYSWKMBDHVN") == "NBDHVKMWSRY"


def test_acci_is_palindromic_and_skips_false_reverse_matches():
    assert rs.enzyme_info("AccI")["palindromic"]
    # GTGAAC matches the old wrong reverse pattern GT[GT][AC]AC but is not an AccI site GT[AC][GT]AC
    assert rs.find_sites("AAAAGTGAACAAAA", "AccI") == []
    assert len(rs.find_sites("AAAAGTAGACAAAA", "AccI")) == 1


def test_linear_drops_cuts_outside_molecule():
    info = rs.enzyme_info("MmeI")
    seq = info["site"].replace("N", "A") + "A" * 5  # site near the end: downstream cut falls off a linear molecule
    for h in rs.find_sites(seq, "MmeI"):
        assert 0 < h["cut_top"] < len(seq) and 0 < h["cut_bottom"] < len(seq)
