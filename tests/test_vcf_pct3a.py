from sugarcode.bio.vcf import unescape_value


def test_colon_escape_decoded():
    assert unescape_value("ClinGen%3ACA1") == "ClinGen:CA1"
    assert unescape_value("a%2Bb") == "a%2Bb"  # not a VCF 4.3 escape; left as-is
