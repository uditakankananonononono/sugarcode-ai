"""Regression: unmapped read placed at mate position (bwa style) has no alignment end (found vs pysam on NA12878 chr20)."""
from sugarcode.bio import sam as S

HDR = "@SQ\tSN:20\tLN:63025520\n"


def test_unmapped_with_cigar_has_no_end():
    rec = "r1\t181\t20\t1006807\t0\t35M66S\t=\t1006807\t0\t" + "A" * 101 + "\t" + "I" * 101 + "\n"
    r = S.parse_sam(HDR + rec)["records"][0]
    assert S.alignment_end(r) is None


def test_mapped_end_unchanged():
    rec = "r2\t121\t20\t1006807\t0\t66S35M\t=\t1006807\t0\t" + "A" * 101 + "\t" + "I" * 101 + "\n"
    r = S.parse_sam(HDR + rec)["records"][0]
    assert S.alignment_end(r) == 1006841
