"""GFF3/GTF toolkit: parse, roundtrip, hierarchy, overlap, filters, rows."""
import pytest

from sugarcode.bio.gff import (parse_gff, write_gff, children_of,
                               descendants_of, overlaps, query_region, stats,
                               filter_records, records_to_rows,
                               escape_attr, unescape_attr)

GFF3 = """##gff-version 3
##sequence-region chr1 1 2000
chr1	test	gene	100	900	.	+	.	ID=g1;Name=Foo%20Kinase
chr1	test	mRNA	100	900	.	+	.	ID=t1;Parent=g1
chr1	test	exon	100	200	.	+	.	Parent=t1
chr1	test	exon	800	900	.	+	.	Parent=t1
chr1	test	CDS	150	200	5.5	+	0	Parent=t1
chr2	test	gene	50	60	.	-	.	ID=g2;Name=Other
"""

GTF = ('chr1\thavana\tgene\t100\t900\t.\t+\t.\t'
       'gene_id "g1"; gene_name "Foo";\n'
       'chr1\thavana\ttranscript\t100\t900\t.\t+\t.\t'
       'gene_id "g1"; transcript_id "t1";\n')


def test_parse_gff3_records_and_attrs():
    g = parse_gff(GFF3)
    assert g["format"] == "gff3" and len(g["records"]) == 6
    r0 = g["records"][0]
    assert r0["seqid"] == "chr1" and r0["start"] == 100 and r0["end"] == 900
    assert r0["attributes"]["ID"] == ["g1"]
    assert r0["attributes"]["Name"] == ["Foo Kinase"]   # unescaped
    assert g["records"][4]["score"] == 5.5 and g["records"][4]["phase"] == 0
    assert g["records"][5]["strand"] == "-"


def test_gff3_roundtrip_exact():
    g = parse_gff(GFF3)
    assert write_gff(g) == GFF3


def test_gtf_parse_and_roundtrip():
    g = parse_gff(GTF)
    assert g["format"] == "gtf"
    assert g["records"][1]["attributes"]["transcript_id"] == ["t1"]
    assert write_gff(g) == GTF


def test_attr_escape_symmetry():
    s = "a;b=c,d&e% f"
    assert unescape_attr(escape_attr(s)) == s


def test_double_escape_stays_literal():
    assert unescape_attr("%2520") == "%20"      # not a space
    assert unescape_attr("%20") == " "


def test_hierarchy_queries():
    g = parse_gff(GFF3)
    assert [c["type"] for c in children_of(g, "g1")] == ["mRNA"]
    kinds = [d["type"] for d in descendants_of(g, "g1")]
    assert kinds == ["mRNA", "exon", "exon", "CDS"]
    assert descendants_of(g, "g2") == []


def test_overlap_semantics():
    g = parse_gff(GFF3)
    assert overlaps(g["records"][0], "chr1", 900, 950)      # touches end
    assert overlaps(g["records"][0], "chr1", 50, 100)       # touches start
    assert not overlaps(g["records"][0], "chr1", 901, 950)
    assert not overlaps(g["records"][0], "chr2", 100, 900)
    with pytest.raises(ValueError):
        overlaps(g["records"][0], "chr1", 0, 5)


def test_query_region_with_types():
    g = parse_gff(GFF3)
    hits = query_region(g, "chr1", 180, 850)
    assert len(hits) == 5  # gene, mRNA, both exons, CDS (180 <= 200)
    cds = query_region(g, "chr1", 1, 2000, types=["CDS"])
    assert len(cds) == 1 and cds[0]["start"] == 150


def test_stats_summary():
    s = stats(parse_gff(GFF3))
    assert s["records"] == 6
    assert s["by_type"] == {"CDS": 1, "exon": 2, "gene": 2, "mRNA": 1}
    assert s["strands"]["-"] == 1
    assert s["span"]["chr1"] == {"min_start": 100, "max_end": 900}


def test_filter_keeps_children():
    g = parse_gff(GFF3)
    out = filter_records(g, types=["gene"], seqids=["chr1"])
    types = [r["type"] for r in out["records"]]
    assert types == ["gene", "mRNA", "exon", "exon", "CDS"]
    out2 = filter_records(g, types=["gene"], keep_children=False)
    assert [r["type"] for r in out2["records"]] == ["gene", "gene"]


def test_records_to_rows():
    rows = records_to_rows(parse_gff(GFF3))
    assert rows[0]["attr_ID"] == "g1" and rows[1]["attr_Parent"] == "g1"
    assert rows[4]["score"] == 5.5 and rows[5]["phase"] == ""


def test_malformed_inputs_raise():
    with pytest.raises(ValueError, match="need 9"):
        parse_gff("chr1\ta\tgene\n")
    with pytest.raises(ValueError, match="not integers"):
        parse_gff("chr1\ta\tgene\tx\t9\t.\t+\t.\tID=g\n")
    with pytest.raises(ValueError, match="invalid coordinates"):
        parse_gff("chr1\ta\tgene\t9\t5\t.\t+\t.\tID=g\n")
    with pytest.raises(ValueError, match="invalid strand"):
        parse_gff("chr1\ta\tgene\t1\t9\t.\tx\t.\tID=g\n")
    with pytest.raises(ValueError, match="unrecognized attribute syntax"):
        parse_gff("chr1\ta\tgene\t1\t9\t.\t+\t.\tIDg\n")
    with pytest.raises(ValueError, match="no GFF records"):
        parse_gff("##gff-version 3\n")
