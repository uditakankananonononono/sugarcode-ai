"""BED toolkit: parse (BED3-12), roundtrip, merge, GFF conversion, filters."""
import pytest

from sugarcode.bio.bed import (parse_bed, write_bed, overlaps, merge_intervals,
                               to_gff, stats, filter_records)

BED = """track name=demo
chr1	0	100	first	50	+
chr1	50	150	second	80	-
chr1	150	200	touching	10	+
chr2	10	30	blocked	60	+	10	30	255,0,0	2	10,5,	0,15,
"""


def test_parse_bed3_to_bed12():
    b = parse_bed(BED)
    assert len(b["records"]) == 4 and b["header"] == ["track name=demo"]
    r0, r3 = b["records"][0], b["records"][3]
    assert r0 == {"chrom": "chr1", "start": 0, "end": 100,
                  "name": "first", "score": 50.0, "strand": "+"}
    assert r3["thick_start"] == 10 and r3["thick_end"] == 30
    assert r3["item_rgb"] == "255,0,0"
    assert r3["block_count"] == 2 and r3["block_sizes"] == [10, 5]
    assert r3["block_starts"] == [0, 15]


def test_roundtrip_exact():
    assert write_bed(parse_bed(BED)) == BED


def test_block_validation():
    with pytest.raises(ValueError, match="blockCount 2 != 1 sizes"):
        parse_bed("chr1\t0\t100\tx\t0\t+\t0\t100\t0,0,0\t2\t10\t0,15\n")
    with pytest.raises(ValueError, match="first blockStart must be 0"):
        parse_bed("chr1\t0\t100\tx\t0\t+\t0\t100\t0,0,0\t1\t10\t5\n")
    with pytest.raises(ValueError, match="escapes the interval"):
        parse_bed("chr1\t0\t100\tx\t0\t+\t0\t100\t0,0,0\t2\t10,95\t0,10\n")
    with pytest.raises(ValueError, match="invalid 0-based interval"):
        parse_bed("chr1\t100\t100\n")
    with pytest.raises(ValueError, match="score not numeric"):
        parse_bed("chr1\t0\t100\tx\tNaNx\n")


def test_half_open_overlap():
    b = parse_bed(BED)
    r0 = b["records"][0]
    assert overlaps(r0, "chr1", 99, 200)
    assert not overlaps(r0, "chr1", 100, 200)   # end is exclusive
    assert overlaps(r0, "chr1", 0, 1)
    with pytest.raises(ValueError):
        overlaps(r0, "chr1", 5, 5)


def test_merge_bedtools_default_joins_bookended():
    merged = merge_intervals(parse_bed(BED)["records"])
    # bedtools merge -d 0: [0,100)+[50,150)+[150,200) -> [0,200)
    assert merged == [{"chrom": "chr1", "start": 0, "end": 200},
                      {"chrom": "chr2", "start": 10, "end": 30}]


def test_merge_strict_overlap_only():
    merged = merge_intervals(parse_bed(BED)["records"], min_dist=-1)
    assert merged == [{"chrom": "chr1", "start": 0, "end": 150},
                      {"chrom": "chr1", "start": 150, "end": 200},
                      {"chrom": "chr2", "start": 10, "end": 30}]


def test_merge_gap_distance():
    recs = parse_bed("c\t0\t10\nc\t15\t20\n")["records"]
    assert len(merge_intervals(recs)) == 2
    assert merge_intervals(recs, min_dist=5) == [{"chrom": "c", "start": 0, "end": 20}]
    with pytest.raises(ValueError):
        merge_intervals(recs, min_dist=-2)


def test_to_gff_coordinate_math():
    gff_recs = to_gff(parse_bed(BED)["records"][:1])
    r = gff_recs[0]
    assert r["start"] == 1 and r["end"] == 100   # 0-based -> 1-based closed
    assert r["type"] == "region" and r["attributes"]["Name"] == ["first"]
    assert r["score"] == 50.0 and r["strand"] == "+"


def test_stats_summary():
    s = stats(parse_bed(BED))
    assert s["records"] == 4
    assert s["bases_covered"] == 100 + 100 + 50 + 20
    assert s["width"]["max"] == 100 and s["stranded"] == 4


def test_filter_records():
    b = parse_bed(BED)
    assert len(filter_records(b, chroms=["chr2"])["records"]) == 1
    assert len(filter_records(b, min_width=60)["records"]) == 2
    assert len(filter_records(b, min_score=60)["records"]) == 2
