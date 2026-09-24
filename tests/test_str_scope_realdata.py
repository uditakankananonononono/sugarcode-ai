from sugarcode.modules.str_scope.core import find_strs, expansion_call


def test_homopolymer_does_not_hide_compound_repeat():
    # NC_001806.2 (HSV-1) 4125-4173: G-run flank then (GGGGTT)x4
    s = "GGCCCCTCCGGG" + "GGGGTT" * 4 + "GTTGAAGCGGAG"
    hits = [h for h in find_strs(s, 1, 6, 4) if h["unit_len"] == 6]
    assert hits and hits[0]["repeats"] == 4 and hits[0]["canonical_unit"] == "GGGGTT"


def test_adjacent_dinucleotide_runs_both_reported():
    # NG_005905.2 117405-117459: (TA)n directly followed by (CA)7
    s = "ATATGTTATATATATATATA" + "CA" * 7 + "TATATATGTATATATATATA"
    units = {h["canonical_unit"] for h in find_strs(s, 2, 2, 7)}
    assert {"AT", "AC"} <= units


def test_locus_bands_genereviews():
    assert expansion_call(27, 26, "CAG", "HTT")["classification"] == "intermediate range"
    assert expansion_call(38, 26, "CAG", "HTT")["classification"].startswith("reduced-penetrance")
    assert expansion_call(40, 26, "CAG", "HTT")["classification"].startswith("full-penetrance")
    assert expansion_call(26, 26, "CAG", "HTT")["classification"] == "normal range"
    assert expansion_call(80, 44, "CGG", "FMR1")["classification"] == "premutation range"
    assert expansion_call(201, 44, "CGG", "FMR1")["classification"] == "full mutation range"
    # no locus: legacy behaviour unchanged
    assert expansion_call(80, 44, "CGG")["classification"].startswith("expanded")
