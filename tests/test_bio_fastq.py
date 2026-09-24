"""FASTQ toolkit: parse, Phred math, stats, filter, trim, conversion."""
import pytest

from sugarcode.bio.fastq import (parse_fastq, write_fastq, detect_offset,
                                 phred_scores, mean_phred, stats,
                                 filter_reads, trim_reads, to_fasta)

# Phred+33: I=40, #=2, 5=20
READS = """@r1 good read
ACGTACGTAC
+
IIIIIIIIII
@r2 low tail
ACGTACGTAC
+
IIII######
@r3 n heavy
ACGTNNNNNN
+
5555555555
"""


def test_parse_and_roundtrip():
    recs = parse_fastq(READS)
    assert len(recs) == 3
    assert recs[0]["id"] == "r1" and recs[0]["description"] == "r1 good read"
    assert recs[0]["sequence"] == "ACGTACGTAC"
    assert write_fastq(recs) == READS


def test_parse_errors():
    with pytest.raises(ValueError, match="must start with '@'"):
        parse_fastq("r1\nACGT\n+\nIIII\n")
    with pytest.raises(ValueError, match="expected '\\+' separator"):
        parse_fastq("@r1\nACGT\nx\nIIII\n")
    with pytest.raises(ValueError, match="lengths differ"):
        parse_fastq("@r1\nACGT\n+\nIII\n")
    with pytest.raises(ValueError, match="non-IUPAC"):
        parse_fastq("@r1\nACG!\n+\nIIII\n")
    with pytest.raises(ValueError, match="no FASTQ records"):
        parse_fastq("\n\n")


def test_phred_decode_and_offset_detection():
    assert phred_scores("I#", 33) == [40, 2]
    assert detect_offset(["IIII"]) is None      # ambiguous: all chars >= 64
    assert detect_offset(["II#I"]) == 33        # '#' proves +33
    with pytest.raises(ValueError, match="baseline"):
        phred_scores("!", 64)                   # '!'=33 is below the +64 baseline
    with pytest.raises(ValueError, match="33 or 64"):
        phred_scores("II", 42)


def test_stats_math():
    recs = parse_fastq(READS)
    s = stats(recs, offset=33)
    assert s["reads"] == 3 and s["bases"] == 30
    assert s["length"] == {"min": 10, "max": 10, "mean": 10.0}
    assert s["mean_phred"] == round((10 * 40 + (4 * 40 + 6 * 2) + 10 * 20) / 30, 2)
    assert s["n_fraction"] == round(6 / 30, 6)
    assert len(s["per_position_mean_phred"]) == 10
    assert s["per_position_mean_phred"][0] == round((40 + 40 + 20) / 3, 2)


def test_stats_offset_ambiguity_note():
    recs = parse_fastq("@r\nACGT\n+\nIIII\n")
    s = stats(recs)
    assert s["offset"] == 33 and s["offset_note"] and "ambiguous" in s["offset_note"]


def test_filter_reads():
    recs = parse_fastq(READS)
    assert [r["id"] for r in filter_reads(recs, min_mean_phred=20)] == ["r1", "r3"]
    assert [r["id"] for r in filter_reads(recs, max_n_frac=0.3)] == ["r1", "r2"]
    assert [r["id"] for r in filter_reads(recs, min_len=11)] == []
    assert len(filter_reads(recs)) == 3


def test_trim_reads_sliding_window():
    recs = parse_fastq(READS)
    out = trim_reads(recs, window=4, min_phred=15, min_len=3)
    ids = [r["id"] for r in out]
    assert "r1" in ids and len(out[ids.index("r1")]["sequence"]) == 10
    # r2: first failing window starts at index 3 (40,2,2,2 -> 11.5 < 15), cut there
    assert out[ids.index("r2")]["sequence"] == "ACG"
    assert "r3" in ids                                  # mean 20 > 15, kept
    dropped = trim_reads(recs, window=4, min_phred=15, min_len=4)
    assert [r["id"] for r in dropped] == ["r1", "r3"]   # r2 trims to 3 < min_len


def test_trim_drops_short_and_bad_window():
    with pytest.raises(ValueError):
        trim_reads(parse_fastq(READS), window=0)


def test_to_fasta():
    fa = to_fasta(parse_fastq(READS))
    assert fa.startswith(">r1 good read\nACGTACGTAC\n")
    assert fa.count(">") == 3
