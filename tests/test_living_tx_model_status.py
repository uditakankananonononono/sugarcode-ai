"""predicted_clinical_success carries a model_status label; its value is unchanged."""
import pytest

from sugarcode.modules.living_tx.core import PAYLOADS, design_living_therapeutic

BEFORE = {"IL-22": 0.796, "IL-10": 0.811, "GLP-1": 0.781,
          "phenylalanine_degradase": 0.826, "oxalate_decarboxylase": 0.826}


@pytest.mark.parametrize("payload", sorted(PAYLOADS))
def test_model_status_label_present_and_value_unchanged(payload):
    r = design_living_therapeutic(payload)
    assert r["model_status"] == "hand-set heuristic, uncalibrated"
    assert r["predicted_clinical_success"] == BEFORE[payload]
