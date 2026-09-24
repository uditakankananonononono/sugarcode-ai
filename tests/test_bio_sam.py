"""SAM toolkit: parse, flags, CIGAR math, roundtrip, stats, filters, BED."""
import pytest

from sugarcode.bio.sam import (parse_sam, write_sam, decode_flags, encode_flags,
                               parse_cigar, cigar_reference_length,
                               cigar_query_length, alignment_end, stats,
                               filter_records, to_bed)

SAM = """@HD	VN:1.6	SO:coordinate
@SQ	SN:chr1	LN:10000
@CO	demo alignments
r001	99	chr1	100	60	10M	=	200	110	ACGTACGTAC	IIIIIIIIII	NM:i:0	AS:i:20
r002	16	chr1	200	25	5S10M2I3D1N4M	*	0	0	ACGTACGTACGTACGTA	IIIIIIIIIIIIIIIII	NM:i:3	XR:Z:note
r003	4	*	0	0	*	*	0	0	NNNN	####
r004	272	chr1	300	10	8M	*	0	0	ACGTACGT	IIIIIIII
"""


def test_parse_header_and_records():
    s = parse_sam(SAM)
    assert s["header"]["HD"] == [{"VN": "1.6", "SO": "coordinate"}]
    assert s["header"]["SQ"] == [{"SN": "chr1", "LN": "10000"}]
    assert s["header"]["CO"] == [{"text": "demo alignments"}]
    r0 = s["records"][0]
    assert r0["qname"] == "r001" and r0["pos"] == 100 and r0["mapq"] == 60
    assert r0["tags"] == {"NM": 0, "AS": 20}
    assert r0["tag_types"] == {"NM": "i", "AS": "i"}
    assert s["records"][1]["tags"]["XR"] == "note"
    assert s["records"][2]["rname"] is None and s["records"][2]["seq"] == "NNNN"


def test_roundtrip_exact():
    assert write_sam(parse_sam(SAM)) == SAM


def test_flag_decode_encode():
    f = decode_flags(99)
    assert f["paired"] and f["proper_pair"] and f["mate_reverse"] and f["read1"]
    assert not f["unmapped"] and not f["reverse"]
    assert encode_flags(paired=True, proper_pair=True, mate_reverse=True,
                        read1=True) == 99
    assert decode_flags(272)["secondary"] and decode_flags(272)["reverse"]
    with pytest.raises(ValueError):
        decode_flags(-1)
    with pytest.raises(ValueError, match="unknown flag"):
        encode_flags(flying=True)


def test_cigar_math():
    ops = parse_cigar("5S10M2I3D1N4M")
    assert ops == [(5, "S"), (10, "M"), (2, "I"), (3, "D"), (1, "N"), (4, "M")]
    assert cigar_reference_length(ops) == 10 + 3 + 1 + 4
    assert cigar_query_length(ops) == 5 + 10 + 2 + 4
    assert parse_cigar("*") == []
    with pytest.raises(ValueError, match="without a length"):
        parse_cigar("M10")
    with pytest.raises(ValueError, match="invalid CIGAR char"):
        parse_cigar("10Z")
    with pytest.raises(ValueError, match="bare length"):
        parse_cigar("10M5")


def test_alignment_end_and_stats():
    s = parse_sam(SAM)
    assert alignment_end(s["records"][0]) == 109
    assert alignment_end(s["records"][1]) == 200 + 18 - 1
    assert alignment_end(s["records"][2]) is None
    st = stats(s)
    assert st["reads"] == 4 and st["mapped"] == 3 and st["unmapped"] == 1
    assert st["mapped_rate"] == 0.75
    assert st["mapq"] == {"min": 10, "max": 60, "mean": 31.67}
    assert st["by_rname"] == {"chr1": 3}
    assert st["proper_pairs"] == 1 and st["secondary"] == 1


def test_filters():
    s = parse_sam(SAM)
    assert len(filter_records(s, mapped_only=True)["records"]) == 3
    assert len(filter_records(s, primary_only=True)["records"]) == 3
    assert [r["qname"] for r in filter_records(s, min_mapq=30)["records"]] == ["r001"]
    assert len(filter_records(s, mapped_only=True, primary_only=True,
                              min_mapq=20)["records"]) == 2


def test_to_bed_coordinate_math():
    beds = to_bed(parse_sam(SAM))
    assert len(beds) == 3                       # unmapped r003 skipped
    assert beds[0] == {"chrom": "chr1", "start": 99, "end": 109,
                       "name": "r001", "score": 60.0, "strand": "+"}
    assert beds[1]["strand"] == "-" and beds[1]["end"] == 199 + 18


def test_malformed_inputs_raise():
    with pytest.raises(ValueError, match="need >= 11"):
        parse_sam("r1\t0\tchr1\n")
    with pytest.raises(ValueError, match="not integers"):
        parse_sam("r1\tx\tchr1\t1\t0\t10M\t*\t0\t0\tA\tI\n")
    with pytest.raises(ValueError, match="mapped record with POS 0"):
        parse_sam("r1\t0\tchr1\t0\t0\t10M\t*\t0\t0\tA\tI\n")
    with pytest.raises(ValueError, match="malformed optional tag"):
        parse_sam("r1\t0\tchr1\t1\t0\t1M\t*\t0\t0\tA\tI\tNM:q:0\n")
    with pytest.raises(ValueError, match="declares i"):
        parse_sam("r1\t0\tchr1\t1\t0\t1M\t*\t0\t0\tA\tI\tNM:i:x\n")
    with pytest.raises(ValueError, match="no SAM alignments"):
        parse_sam("@HD\tVN:1.6\n")
