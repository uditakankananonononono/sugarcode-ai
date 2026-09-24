"""Regression (BUG 44): HGVS c. coordinates must be CDS-relative and full ClinVar names parsed."""
from sugarcode.modules.gene_analysis.core import _variant_features

# synthetic transcript: 12-nt 5'UTR + ATG GAG CGT ... (40 codons) + stop + 3'UTR
UTR5 = "GCCGCCACCAGC"
CDS = "ATG" + "GAG" + "CGT" + "GCT" * 37 + "TAA"
SEQ = UTR5 + CDS + "GCATGCATGC"


def test_c_coordinate_is_cds_relative():
    f = _variant_features({"variant": "c.4G>A", "consequence": "missense"}, SEQ)
    assert f["position"] == len(UTR5) + 4
    assert f["codon"] == "GAG"


def test_full_clinvar_name_ignores_accession_digits():
    f = _variant_features({"variant": "NM_000518.5(HBB):c.7C>T", "consequence": "missense"}, SEQ)
    assert f["position"] == len(UTR5) + 7
    assert f["codon"] == "CGT"


def test_explicit_position_and_bare_numbers_unchanged():
    assert _variant_features({"variant": "c.4G>A", "position": 3}, SEQ)["position"] == 3
    assert _variant_features({"variant": "20"}, SEQ)["position"] == 20
