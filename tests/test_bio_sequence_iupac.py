from sugarcode.bio.sequence import clean_dna, translate, gc_content


def test_ambiguity_codes_do_not_shift_frame():
    # R used to be dropped, turning ATG RCT TAA into ATG CTT AA (M L)
    assert clean_dna("atg rct\ntaa") == "ATGNCTTAA"
    assert translate("ATGRCTTAA") == "MX*"
    assert translate("ATGRCTTAA", to_stop=True) == "MX"


def test_gc_ignores_ambiguous_in_denominator():
    assert gc_content("GGRR") == 1.0
