from sugarcode.modules.neohunter.core import hla_binding
from omega.registry import REGISTRY


def test_binding_discloses_heuristic_and_responds_to_anchors():
    good = hla_binding("LLFGYPVYV", "A*02:01"); bad = hla_binding("KKFGYPVYK", "A*02:01")
    assert good["score"] > bad["score"]
    assert "not a trained predictor" in good["method"]


def test_registry_does_not_claim_prediction_model():
    s = REGISTRY["neohunter"].summary
    assert "not a trained" in s and "heuristic" in s
