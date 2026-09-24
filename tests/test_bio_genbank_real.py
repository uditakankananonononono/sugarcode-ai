"""Regression tests for bio.genbank found by validating against Biopython on
25 NCBI records (mega27-01 benchmarks/sweep_genbank_biopython.json)."""
from sugarcode.bio.genbank import parse_genbank, parse_location

GB = """LOCUS       TEST                 60 bp    DNA     linear   SYN 01-JAN-2000
FEATURES             Location/Qualifiers
     source          1..60
                     /organism="synthetic
                     construct"
     CDS             join(1..9,
                     20..28)
                     /note="a ""quoted"" word"
                     /translation="MKK
                     MKK"
     gene            complement(<30..>45)
     misc_feature    50^51
     polyA_site      60
                     /gene_synonym="A1; B2;
                     C3"
ORIGIN
        1 atgaaaaaar ngggggggga tgaaaaaaac ccccccccct tttttttttg ggggggggga
//
"""


def test_multiline_qualifiers_do_not_leak_into_location():
    f = parse_genbank(GB)["features"]
    assert f[0]["qualifiers"]["organism"] == "synthetic construct"
    assert f[1]["spans"] == [(1, 9), (20, 28)]
    assert f[1]["qualifiers"]["translation"] == "MKKMKK"
    assert f[1]["qualifiers"]["note"] == 'a "quoted" word'
    assert f[4]["spans"] == [(60, 60)]
    assert f[4]["qualifiers"]["gene_synonym"] == "A1; B2; C3"


def test_partial_between_and_complement_locations():
    f = parse_genbank(GB)["features"]
    assert f[2]["spans"] == [(30, 45)] and f[2]["strand"] == -1
    assert f[3]["spans"] == [(50, 50)]
    assert parse_location("join(complement(5..9),complement(1..3))") == ([(5, 9), (1, 3)], -1)
    assert parse_location("join(J00194.1:100..202,1..10)") == ([(1, 10)], 1)


def test_iupac_letters_keep_coordinates():
    seq = parse_genbank(GB)["sequence"]
    assert len(seq) == 60 and seq[9:11] == "RN"
