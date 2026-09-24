"""Pileup toolkit: per-position stacks, indel events, mpileup text, variants."""
import pytest

from sugarcode.bio.sam import parse_sam
from sugarcode.bio.pileup import pileup, to_mpileup, variant_sites

SAM = """@HD\tVN:1.6\tSO:coordinate
@SQ\tSN:chr1\tLN:100
r1\t0\tchr1\t1\t60\t4M\t*\t0\t0\tACGT\tIIII
r2\t0\tchr1\t2\t30\t2M1I2M\t*\t0\t0\tGTACA\tIIIII
r3\t16\tchr1\t3\t20\t3M1D1M\t*\t0\t0\tGGCC\tIIII
r4\t4\t*\t0\t0\t*\t*\t0\t0\t*\t*
"""


def _rows(sam_text=SAM, **kw):
    return pileup(parse_sam(sam_text), **kw)


def test_m_positions_stack_with_strand_case():
    rows = _rows()
    by = {r["pos"]: r for r in rows}
    assert by[1]["counts"] == {"A": 1} and by[1]["depth"] == 1
    assert by[2]["counts"] == {"C": 1, "G": 1}
    assert by[3]["counts"] == {"G": 1, "T": 1, "g": 1}   # r3 is reverse
    assert by[4]["counts"] == {"T": 1, "C": 1, "g": 1}
    assert by[5]["counts"] == {"A": 1, "c": 1}
    assert by[7]["counts"] == {"c": 1}
    assert by[1]["mapq_mean"] == 60.0 and by[3]["mapq_mean"] == 36.667
    assert by[1]["qual_mean"] == 40.0


def test_insertion_anchors_to_preceding_position():
    by = {r["pos"]: r for r in _rows()}
    assert by[3]["insertions"] == {"+1A": 1}
    assert all(not r["insertions"] for p, r in by.items() if p != 3)


def test_deletion_event_and_star_bases():
    by = {r["pos"]: r for r in _rows()}
    assert by[5]["deletions"] == {"-1N": 1}
    assert by[6]["counts"] == {"*": 1} and by[6]["del_depth"] == 1
    assert by[6]["depth"] == 1                            # samtools counts *
    assert by[6]["qual_mean"] is None                     # no base quals at del


def test_skipped_region_consumes_reference_silently():
    sam = ("@SQ\tSN:chr1\tLN:100\n"
           "r1\t0\tchr1\t1\t60\t2M3N2M\t*\t0\t0\tACGT\tIIII\n")
    by = {r["pos"]: r for r in _rows(sam)}
    assert set(by) == {1, 2, 6, 7}                        # 3-5 are the intron


def test_unmapped_and_filters():
    rows = _rows()                                        # r4 unmapped skipped
    assert all(r["depth"] >= 1 for r in rows) and len(rows) == 7
    rows = _rows(min_mapq=25)
    by = {r["pos"]: r for r in rows}
    assert by[3]["counts"] == {"G": 1, "T": 1}            # r3 (mapq 20) gone
    with pytest.raises(ValueError):
        pileup(parse_sam(SAM), min_mapq=-1)
    rows = _rows(min_baseq=41)                            # all M quals are 40
    by = {r["pos"]: r for r in rows}                      # dels have no quals
    assert set(by) == {3, 5, 6}                        # ins/del anchors + star
    assert by[6]["counts"] == {"*": 1} and by[5]["deletions"] == {"-1N": 1}
    assert by[3]["insertions"] == {"+1A": 1} and by[3]["depth"] == 0
    assert by[5]["depth"] == 0 and by[5]["mapq_mean"] is None


def test_rname_filter():
    rows = _rows(rname="chrZ")
    assert rows == []


def test_mpileup_text_shape():
    text = to_mpileup(_rows())
    lines = text.rstrip("\n").split("\n")
    assert len(lines) == 7
    f = lines[2].split("\t")
    assert f[:4] == ["chr1", "3", "N", "3"] and "+1A" in f[4]
    assert lines[5].split("\t")[4] == "*"


def test_variant_sites_reference_free():
    sites = variant_sites(_rows(), min_depth=2, min_alt_fraction=0.3)
    by = {s["pos"]: s for s in sites}
    assert by[2] == {"rname": "chr1", "pos": 2, "ref_base": "C",
                     "alt_base": "G", "depth": 2, "alt_count": 1,
                     "alt_fraction": 0.5}
    assert 6 not in by                                    # '*' is not ACGT
    assert variant_sites(_rows(), min_depth=2, min_alt_fraction=0.6) == []
