import random

import pytest

from sugarcode.self_improve.engine import SelfImprovementEngine
from sugarcode.self_improve.evidence import GapObservation, preview_evidence


def observation(signature="gap", task="task", partition="development", outcome="fail", ref="receipt"):
    return GapObservation("m", signature, task, partition, outcome, ref)


def test_duplicate_replay_does_not_win_priority():
    repeated = [observation("noisy")] * 100
    independent = [observation("independent", f"task-{n}") for n in range(2)]
    result = preview_evidence("m", repeated + independent)
    assert [r["signature"] for r in result] == ["independent", "noisy"]
    assert result[1]["reported_observations"] == 100
    assert result[1]["development_fail_tasks"] == 1


def test_held_out_failure_cannot_be_erased_by_development_passes():
    result = preview_evidence("m", [observation("regression", "hidden", "held_out")]
        + [observation("regression", f"pass-{n}", outcome="pass") for n in range(50)]
        + [observation("development", f"fail-{n}") for n in range(50)])
    assert result[0]["signature"] == "regression"
    assert result[0]["held_out_fail_tasks"] == 1
    assert result[0]["development_pass_tasks"] == 50
    assert "not_authenticated" in result[0]["status"]


def test_partitions_and_outcomes_cannot_conflict():
    with pytest.raises(ValueError, match="overlaps"):
        preview_evidence("m", [observation(), observation("different", partition="held_out")])
    with pytest.raises(ValueError, match="conflicting"):
        preview_evidence("m", [observation(), observation(outcome="pass")])


def test_order_is_deterministic_and_references_retained():
    rows = [observation("b", "task", ref="z"), observation("a", "task", ref="b"),
            observation("b", "task", ref="a")]
    expected = preview_evidence("m", rows)
    for seed in range(10):
        shuffled = rows.copy()
        random.Random(seed).shuffle(shuffled)
        assert preview_evidence("m", shuffled) == expected
    assert expected[1]["source_refs"] == ["a", "z"]


def test_preview_does_not_write_plan_or_activate(tmp_path):
    engine = SelfImprovementEngine(module_id=1, module_slug="m", state_dir=tmp_path)
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert engine.preview_gap_evidence([observation()])[0]["distinct_tasks"] == 1
    after = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert before == after
    assert engine.registry.proposals() == {}


@pytest.mark.parametrize("field,value", [("task_id", ""), ("task_id", "x" * 513),
    ("source_ref", None), ("partition", "test"), ("outcome", True), ("signature", " ")])
def test_invalid_record_domains(field, value):
    fields = {"module_slug": "m", "signature": "gap", "task_id": "task",
              "partition": "development", "outcome": "fail", "source_ref": "receipt"}
    fields[field] = value
    with pytest.raises(ValueError):
        GapObservation(**fields)


def test_invalid_preview_domains():
    assert preview_evidence("m", []) == []
    for rows in ([object()], [observation()] * 10001, (observation(),)):
        with pytest.raises(ValueError):
            preview_evidence("m", rows)
    with pytest.raises(ValueError, match="mismatch"):
        preview_evidence("other", [observation()])
