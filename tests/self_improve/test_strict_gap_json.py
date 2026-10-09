import json
from decimal import Decimal

import pytest

from sugarcode.self_improve.events import GapEvent, GapEventStore
from sugarcode.self_improve.json_values import InvalidTelemetryValue, snapshot_json
from sugarcode.self_improve.plans import FeaturePlan
from sugarcode.self_improve.testsynth import synthesize_tests


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"),
                                  Decimal("NaN"), Decimal(1), {1: "value"}])
def test_invalid_values_never_append(tmp_path, value):
    store = GapEventStore(tmp_path)
    store.append(GapEvent("m", "good"))
    path = tmp_path / "m.gap-events.jsonl"
    before = path.read_bytes()
    with pytest.raises(InvalidTelemetryValue):
        store.append(GapEvent("m", "bad", exemplar={"nested": [value]}))
    assert path.read_bytes() == before


def test_cycles_and_custom_methods_are_not_executed():
    cycle = []
    cycle.append(cycle)
    with pytest.raises(InvalidTelemetryValue, match="cyclic"):
        snapshot_json(cycle)

    class Hostile:
        def __str__(self) -> str:
            raise AssertionError("str called")

        def __repr__(self):
            pytest.fail("repr called")

        def __deepcopy__(self, memo):
            pytest.fail("deepcopy called")

    with pytest.raises(InvalidTelemetryValue):
        snapshot_json(Hostile())


def test_exact_builtin_policy_and_shared_containers():
    class Number(float):
        pass

    with pytest.raises(InvalidTelemetryValue):
        snapshot_json(Number(1))
    shared = [1, True, None, "NaN"]
    result = snapshot_json({"a": shared, "b": shared, "tuple": (2.5,)})
    assert result == {"a": shared, "b": shared, "tuple": [2.5]}
    assert result["a"] is not result["b"]
    assert result["a"] is not shared


def test_depth_and_alias_expansion_are_bounded():
    deep = []
    for _ in range(66):
        deep = [deep]
    with pytest.raises(InvalidTelemetryValue, match="limit"):
        snapshot_json(deep)
    shared = [0] * 100
    with pytest.raises(InvalidTelemetryValue, match="limit"):
        snapshot_json([shared] * 100)


@pytest.mark.parametrize("at", [True, float("nan"), float("inf"), "1", None, 10**1000, -10**1000])
def test_timestamp_contract(at):
    with pytest.raises(InvalidTelemetryValue):
        GapEvent("m", "x", at=at)


@pytest.mark.parametrize("row", ["{bad", '{"module_slug":"m","signature":"x","exemplar":NaN}',
    '{"module_slug":"m","signature":"x","at":Infinity}',
    '{"module_slug":"wrong","signature":"x"}',
    '{"module_slug":"m","signature":1}', "[]"])
def test_historical_rows_fail_closed_without_rewrite(tmp_path, row):
    store = GapEventStore(tmp_path)
    path = tmp_path / "m.gap-events.jsonl"
    contents = json.dumps({"module_slug": "m", "signature": "valid"}) + "\n" + row + "\n"
    path.write_text(contents)
    with pytest.raises(InvalidTelemetryValue, match="row 2"):
        store.all("m")
    assert path.read_text() == contents


def test_roundtrip_and_historical_defaults(tmp_path):
    store = GapEventStore(tmp_path)
    store.append(GapEvent("m", "x", exemplar={"a": (1, 2.5)}, at=0))
    assert store.all("m")[0].exemplar == {"a": [1, 2.5]}
    path = tmp_path / "m.gap-events.jsonl"
    with path.open("a") as stream:
        stream.write('{"module_slug":"m","signature":"legacy"}\n')
    assert store.all("m")[1].at == 0.0


def test_direct_sample_boundary():
    plan = FeaturePlan(module_slug="m", description="filter grants", name="filter", kind="keyword_filter", gap_signature="x",
                       params={"keywords": ["grant"]})
    with pytest.raises(InvalidTelemetryValue):
        synthesize_tests(plan, [float("nan")])
    cycle = []
    cycle.append(cycle)
    with pytest.raises(InvalidTelemetryValue):
        synthesize_tests(plan, cycle)
    source = synthesize_tests(plan, ["grant", {"a": (1, 2)}])
    compile(source, "generated", "exec")


def test_engine_rejects_bad_input_then_valid_cycle_still_works(tmp_path):
    from sugarcode.self_improve.engine import SelfImprovementEngine

    engine = SelfImprovementEngine(module_id=1, module_slug="m", state_dir=tmp_path)
    cycle = []
    cycle.append(cycle)
    for value in (cycle, float("nan"), Decimal("Infinity")):
        with pytest.raises(InvalidTelemetryValue):
            engine.record_gap("filter grants", exemplar=value)
    assert engine.store.all("m") == []
    assert engine.ledger() == []
    for _ in range(2):
        engine.record_gap("filter only biology grants", detail="user keeps asking to filter grants", exemplar="a biology grant for phd students")
    result = engine.run_cycle()
    assert len(result["proposals"]) == 1
    assert result["candidates"][0]["tests_passed"]


def test_invalid_history_does_not_create_candidate_or_proposal(tmp_path):
    from sugarcode.self_improve.engine import SelfImprovementEngine

    engine = SelfImprovementEngine(module_id=1, module_slug="m", state_dir=tmp_path)
    path = tmp_path / "gap-events" / "m.gap-events.jsonl"
    path.write_text('{"module_slug":"m","signature":"filter grants","exemplar":NaN}\n')
    with pytest.raises(InvalidTelemetryValue):
        engine.run_cycle()
    assert engine.registry.proposals() == {}
    assert engine.ledger() == []
