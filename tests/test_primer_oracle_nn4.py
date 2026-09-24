"""Oracle: tm_nn equals Biopython Tm_NN with the DNA_NN4 table (edge cases:
5'-T plus 3'-A, all-A/T). Validated on 5,404 RefSeq 20-mers in mega27-01."""
import pytest
from sugarcode.bio.primer import tm_nn


def test_tm_nn_matches_biopython_nn4_both_ends():
    mt = pytest.importorskip("Bio.SeqUtils.MeltingTemp")
    for o in ["TTTTTTTTTTAAAAAAAAAA", "TACGTACGTACGTACGTACA", "ACGTACGTACGTACGTACGT", "GGGCCCGGGCCCAAATTTGC"]:
        ref = mt.Tm_NN(o, dnac1=25, dnac2=25, Na=50, saltcorr=5, nn_table=mt.DNA_NN4)
        assert abs(tm_nn(o) - ref) < 1e-6


def test_hairpin_dg_primer3():
    pytest.importorskip("primer3")
    from sugarcode.bio.primer import hairpin_dg
    strong = hairpin_dg("GGGGCCCCTTTTGGGGCCCC")
    assert strong < -2.0
    assert hairpin_dg("ACGTACGTACGTACGTACGT") > strong
