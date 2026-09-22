import pytest

from sugarcode.modules.oncocircuit import PAYLOADS, TUMOR_PROMOTERS, design_oncocircuit


def test_cancer_specific_promoter_selection_and_annotations():
    result = design_oncocircuit("prostate")
    assert result["promoters"] == ["PSA", "Survivin"]
    assert result["promoter_annotations"][0]["tumor_selectivity"] == TUMOR_PROMOTERS["PSA"]["tumor_selectivity"]


def test_dual_input_gate_suppresses_single_positive_cells():
    result = design_oncocircuit("breast", payload="IL-12")
    gate = result["circuit"]["gates"][0]
    assert result["logic"] == "AND (dual-input)"
    assert gate["logic"] == "AND" and len(gate["inputs"]) == 2
    assert result["simulation"]["output_tumor"] > result["simulation"]["output_single_positive"] * 20
    assert result["tumor_selectivity_fold"] > 100
    assert result["leakage_fraction"] < 0.05


def test_single_input_comparator_really_has_one_input():
    result = design_oncocircuit("unknown cancer", payload="dtA", two_input=False)
    assert result["promoters"] == ["hTERT"]
    assert len(result["circuit"]["gates"][0]["inputs"]) == 1
    assert result["simulation"]["output_single_positive"] == result["simulation"]["output_tumor"]
    assert "lacks the second-input safety constraint" in result["molecular_mechanism"]


def test_payload_mechanism_delivery_and_honest_model_status():
    result = design_oncocircuit("hepatocellular", payload="HSV-TK")
    assert result["payload_action"] == PAYLOADS["HSV-TK"]
    assert "ganciclovir" in result["molecular_mechanism"]
    assert "AAV or LNP" in result["delivery"]
    assert "experimental validation" in result["model_status"]


def test_validation_errors_are_informative():
    with pytest.raises(ValueError, match="non-empty"):
        design_oncocircuit("")
    with pytest.raises(ValueError, match="unknown payload"):
        design_oncocircuit("breast", payload="magic")
