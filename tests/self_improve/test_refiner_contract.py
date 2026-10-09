from dataclasses import replace

import pytest

from sugarcode.self_improve.detector import CapabilityGap
from sugarcode.self_improve.engine import SelfImprovementEngine
from sugarcode.self_improve.planner import FeaturePlanner


def gap():
    return CapabilityGap(module_slug="m", signature="filter grants", occurrences=2,
                         kinds=("feature_request",), exemplars=(), detail="filter grants",
                         first_seen=1, last_seen=2, severity=0.5)


class Refiner:
    def __init__(self, hook):
        self.hook = hook

    def refine(self, plan, gap):
        return self.hook(plan)


@pytest.mark.parametrize("field,value", [("kind", "execute_shell"), ("name", "../bad")])
def test_mutated_frozen_plan_is_rechecked(field, value):
    def hook(plan):
        object.__setattr__(plan, field, value)
        return plan

    with pytest.raises(ValueError):
        FeaturePlanner(Refiner(hook)).plan(gap())


@pytest.mark.parametrize("field", ["module_slug", "gap_signature", "name", "kind"])
def test_valid_plan_cannot_be_retargeted(field):
    with pytest.raises(ValueError, match="identity"):
        FeaturePlanner(Refiner(lambda plan: replace(plan, **{field: "scoring_rule" if field == "kind" else "other"}))).plan(gap())


@pytest.mark.parametrize("result", [None, {}, "plan"])
def test_wrong_return_type_is_refused(result):
    with pytest.raises(ValueError, match="FeaturePlan"):
        FeaturePlanner(Refiner(lambda plan: result)).plan(gap())


def test_allowed_description_and_parameters_are_preserved():
    result = FeaturePlanner(Refiner(lambda plan: replace(
        plan, description="specific filter", params={"keywords": ["biology"]}))).plan(gap())
    assert result.description == "specific filter"
    assert result.params == {"keywords": ["biology"]}


def test_hook_exception_propagates():
    def hook(plan):
        raise RuntimeError("model unavailable")

    with pytest.raises(RuntimeError, match="model unavailable"):
        FeaturePlanner(Refiner(hook)).plan(gap())


def test_public_cycle_refuses_before_candidate_or_proposal(tmp_path):
    planner = FeaturePlanner(Refiner(lambda plan: replace(plan, module_slug="other")))
    engine = SelfImprovementEngine(module_id=1, module_slug="m", state_dir=tmp_path,
                                  planner=planner)
    for _ in range(2):
        engine.record_gap("filter grants", exemplar="biology grant")
    with pytest.raises(ValueError, match="identity"):
        engine.run_cycle()
    assert engine.registry.proposals() == {}
    assert engine._candidates == {}
    assert not any(row["event"] == "feature_planned" for row in engine.ledger())
