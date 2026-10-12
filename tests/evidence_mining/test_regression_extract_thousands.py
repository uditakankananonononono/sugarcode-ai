"""Regression test for behavior at base revision 99cb2d32."""
from sugarcode.modules.evidence_mining import extract_text_evidence


def test_sample_size_parses_thousands_separators():
    # Live PubMed abstract 37185680 said "enrolled 3,649 women"; old code returned 3.
    assert extract_text_evidence("The trial enrolled 3,649 women with 5-year follow-up.")["sample_size"] == 3649
    # old code returned 200
    assert extract_text_evidence("A total of 1,200 patients were included.")["sample_size"] == 1200
    assert extract_text_evidence("n = 1,234,567 participants")["sample_size"] == 1234567
    # plain numbers and non-thousands commas are unchanged
    assert extract_text_evidence("We randomized 120 patients.")["sample_size"] == 120
    assert extract_text_evidence("n=80")["sample_size"] == 80
    assert extract_text_evidence("enrolled 12,34 in total")["sample_size"] == 12
