"""VCF toolkit: parse, roundtrip write, stats, filters, CSV rows."""
import pytest

from sugarcode.bio.vcf import (parse_vcf, write_vcf, variant_type,
                               is_transition, stats, filter_records,
                               records_to_rows, escape_value, unescape_value)

MINI = """##fileformat=VCFv4.2
##contig=<ID=chr1,length=1000>
##INFO=<ID=DP,Number=1,Type=Integer,Description="Total Depth">
##INFO=<ID=AF,Number=A,Type=Float,Description="Allele Frequency">
##INFO=<ID=DB,Number=0,Type=Flag,Description="dbSNP membership">
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##FORMAT=<ID=GQ,Number=1,Type=Integer,Description="Genotype Quality">
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	S1	S2
chr1	100	rs1	A	G	50	PASS	DP=30;AF=0.5;DB	GT:GQ	0/1:99	1/1:90
chr1	200	.	AT	A	12.5	LowQual	DP=8	GT:GQ	0/1:40	0/0:40
chr1	300	.	C	T	80	PASS	DP=25	GT:GQ	0/0:99	0/1:99
chr1	350	.	G	C	60	PASS	DP=22	GT:GQ	0/1:88	0/1:77
chr1	400	.	G	<DEL>	.	.	SVTYPE=DEL	GT	./.	./.
"""


def test_parse_fields_and_typed_info():
    v = parse_vcf(MINI)
    assert v["fileformat"] == "VCFv4.2" and v["samples"] == ["S1", "S2"]
    assert len(v["records"]) == 5
    r0 = v["records"][0]
    assert r0["chrom"] == "chr1" and r0["pos"] == 100 and r0["id"] == "rs1"
    assert r0["alts"] == ["G"] and r0["qual"] == 50.0
    assert r0["info"]["DP"] == 30 and isinstance(r0["info"]["DP"], int)
    assert r0["info"]["AF"] == "0.5"  # Number=A stays text; only Number=1 coerces
    assert r0["info"]["DB"] is True
    assert r0["samples"]["S2"] == {"GT": "1/1", "GQ": "90"}
    assert v["records"][1]["id"] is None and v["records"][4]["qual"] is None
    assert v["records"][4]["filters"] == []


def test_roundtrip_is_exact():
    v = parse_vcf(MINI)
    assert write_vcf(v) == MINI
    assert parse_vcf(write_vcf(v))["records"] == v["records"]


def test_percent_escape_symmetry():
    s = "a;b=c,d% e"
    assert unescape_value(escape_value(s)) == s
    assert unescape_value("%2520") == "%20"     # literal, not a space
    assert unescape_value("%20") == " "


def test_variant_type_cases():
    assert variant_type("A", "G") == "snp"
    assert variant_type("AT", "GC") == "mnp"
    assert variant_type("A", "ATT") == "insertion"
    assert variant_type("ATT", "A") == "deletion"
    assert variant_type("G", "<DEL>") == "symbolic"
    assert variant_type("G", "G[chr2:100[") == "breakend"
    assert is_transition("A", "G") and not is_transition("G", "C")


def test_stats_math():
    s = stats(parse_vcf(MINI))
    assert s["records"] == 5
    assert s["by_type"] == {"deletion": 1, "snp": 3, "symbolic": 1}
    assert s["snps"] == {"transitions": 2, "transversions": 1, "ti_tv": 2.0}
    assert s["filters"] == {"LowQual": 1, "PASS": 3, ".": 1}
    assert s["samples"]["S1"]["0/1"] == 3 and s["samples"]["S2"]["./."] == 1


def test_filter_combinations():
    v = parse_vcf(MINI)
    assert len(filter_records(v, pass_only=True)["records"]) == 4  # PASS + missing(.)
    assert len(filter_records(v, min_qual=50)["records"]) == 3
    assert len(filter_records(v, types=["snp"])["records"]) == 3
    assert len(filter_records(v, chroms=["chr9"])["records"]) == 0
    assert len(filter_records(v, pass_only=True, min_qual=60)["records"]) == 2


def test_records_to_rows_flattening():
    v = parse_vcf(MINI)
    rows = records_to_rows(v, sample="S1")
    assert rows[0]["info_DP"] == 30 and rows[0]["info_DB"] == "true"
    assert rows[1]["info_AF"] == "" and rows[0]["fmt_GQ"] == "99"
    assert rows[4]["filter"] == "" and rows[4]["alt"] == "<DEL>"
    with pytest.raises(ValueError, match="unknown sample"):
        records_to_rows(v, sample="NOPE")


def test_malformed_inputs_raise():
    with pytest.raises(ValueError, match="#CHROM"):
        parse_vcf("chr1\t100\t.\tA\tG\t.\t.\t.\n")
    with pytest.raises(ValueError, match="need >= 8"):
        parse_vcf("#CHROM\tPOS\nchr1\t100\n")
    with pytest.raises(ValueError, match="not an integer"):
        parse_vcf("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
                  "chr1\tabc\t.\tA\tG\t.\t.\t.\n")
    with pytest.raises(ValueError, match="FORMAT keys"):
        parse_vcf("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS1\n"
                  "chr1\t1\t.\tA\tG\t.\t.\t.\tGT:GQ\t0/1\n")
