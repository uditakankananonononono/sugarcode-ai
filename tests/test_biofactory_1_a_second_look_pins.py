"""Unit 31 second-look pins (tests only, PARTIAL): survivors of an independent AST-mutation sweep of
biofactory_1_a/boundary_ops.py. Values are hand-derived literals from the module's documented limits
(MAX_STEPS=10_000, _PRE=1e15, MAX_VALUE=1e6). Exact refusal messages are matched. Toy engineering arithmetic only."""
import pytest
from sugarcode.modules.biofactory_1_a import boundary_ops as b

STEP = {"op": "x"}


def msg(fn, exc, *a, **k):
    with pytest.raises(exc) as e:
        fn(*a, **k)
    return str(e.value)


def test_num_magnitude_cap_and_finite_messages_through_setpoint():
    f = lambda sp: b.pid_control_checked(sp, [1.0])
    assert msg(f, ValueError, 10**15) == "setpoint must be between -1e+06 and 1e+06"        # exactly 1e15: range, not magnitude
    assert msg(f, ValueError, 10**15 + 1) == "setpoint magnitude too large"
    assert msg(f, ValueError, 1e15) == "setpoint must be between -1e+06 and 1e+06"
    assert msg(f, ValueError, 1e16) == "setpoint magnitude too large"
    assert msg(f, ValueError, float("inf")) == "setpoint must be finite"                    # not 'magnitude too large'
    assert msg(f, ValueError, float("-inf")) == "setpoint must be finite"
    assert msg(f, ValueError, float("nan")) == "setpoint must be finite"
    assert msg(f, ValueError, 1e6 + 1) == "setpoint must be between -1e+06 and 1e+06"
    assert msg(f, TypeError, True) == "setpoint must be a number, not bool"
    assert msg(f, TypeError, "1") == "setpoint must be a number"


def test_series_type_message():
    assert msg(b.pid_control_checked, TypeError, 1.0, "abc") == "measurements must be a list or tuple of numbers"
    assert msg(b.pid_control_checked, TypeError, 1.0, {1: 2}) == "measurements must be a list or tuple of numbers"


def test_workflow_dag_step_count_bounds():
    assert len(b.workflow_dag_checked([STEP])["nodes"]) == 1
    assert len(b.workflow_dag_checked([STEP] * 10_000)["nodes"]) == 10_000
    assert msg(b.workflow_dag_checked, ValueError, []) == "steps must have 1..10000 entries"
    assert msg(b.workflow_dag_checked, ValueError, [STEP] * 10_001) == "steps must have 1..10000 entries"


def _dag(n, e):
    return {"nodes": [{"id": i} for i in range(n)], "edges": [{"source": 0} for _ in range(e)]}


def test_reroute_dag_shape_messages():
    for d in ({"nodes": [{"id": 0}]}, {"edges": []}, {}, [], None, "x"):
        assert msg(b.reroute_on_failure_checked, TypeError, d, 0, {"op": "y"}) == "dag must be a mapping with nodes and edges"
    for d in ({"nodes": "ab", "edges": []}, {"nodes": [{"id": 0}], "edges": "ab"}, {"nodes": {}, "edges": []}):
        assert msg(b.reroute_on_failure_checked, TypeError, d, 0, {"op": "y"}) == "dag nodes and edges must be lists"


def test_reroute_dag_size_bounds():
    ok = b.reroute_on_failure_checked(_dag(1, 0), 0, {"op": "y"})
    assert isinstance(ok, dict)
    b.reroute_on_failure_checked(_dag(10_000, 0), 0, {"op": "y"})
    b.reroute_on_failure_checked(_dag(1, 10_000), 0, {"op": "y"})
    m = "dag must have 1..10000 nodes and at most 10000 edges"
    assert msg(b.reroute_on_failure_checked, ValueError, _dag(0, 0), 0, {"op": "y"}) == m
    assert msg(b.reroute_on_failure_checked, ValueError, _dag(10_001, 0), 0, {"op": "y"}) == m
    assert msg(b.reroute_on_failure_checked, ValueError, _dag(1, 10_001), 0, {"op": "y"}) == m
