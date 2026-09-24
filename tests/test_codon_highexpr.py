from sugarcode.bio.codon import ECOLI_HIGHEXPR, HOST_TABLES, cai, relative_adaptiveness

def test_highexpr_table_loaded_and_registered():
    assert HOST_TABLES["ecoli_highexpr"] is ECOLI_HIGHEXPR
    w = relative_adaptiveness(ECOLI_HIGHEXPR)
    # highly expressed E. coli genes strongly prefer CUG (Leu) and AAA (Lys)
    assert w["CTG"] == 1.0 and w["AAA"] == 1.0
    assert w["CTA"] < 0.1

def test_highexpr_cai_ranks_optimal_above_rare():
    good = "CTGAAAGAAGCTCGTGGT" * 5
    bad = "CTAAAGGAGGCGAGGGGG" * 5
    assert cai(good, ECOLI_HIGHEXPR) > 0.8 > cai(bad, ECOLI_HIGHEXPR)
