import pytest
from sugarcode.modules.neohunter.core import hla_binding_iedb

def test_known_a0201_epitope_scores_as_binder():
    # influenza M1 58-66 GILGFVFTL is a classic HLA-A*02:01 epitope
    assert hla_binding_iedb("GILGFVFTL", "A*02:01")["p_binder_ic50_500nM"] > 0.7

def test_charged_peptide_low_for_a0201():
    assert hla_binding_iedb("DDDDDDDDD", "A*02:01")["p_binder_ic50_500nM"] < 0.2

def test_b0702_prefers_proline_p2():
    # B*07:02 epitope from CMV pp65: TPRVTGGGAM is 10-mer; use 9-mer RPHERNGFTV
    assert hla_binding_iedb("RPHERNGFT", "B*07:02")["p_binder_ic50_500nM"] > hla_binding_iedb("RDHERNGFT", "B*07:02")["p_binder_ic50_500nM"]

def test_rejects_bad_length():
    with pytest.raises(ValueError):
        hla_binding_iedb("GILGFVF", "A*02:01")
