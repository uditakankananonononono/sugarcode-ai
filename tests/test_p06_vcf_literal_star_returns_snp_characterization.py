"""P06: literal-star-returns-snp characterization (authored, NOT RUN).

Pins only the label that the current implementation returns for one synthetic
input. It is not a statement about correct handling of the '*' allele.
"""
from sugarcode.bio.vcf import variant_type


def test_variant_type_literal_star_alt_returns_snp_label():
    assert variant_type("A", "*") == "snp"
