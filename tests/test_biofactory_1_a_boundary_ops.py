import json
import math
import pytest

from sugarcode.modules.biofactory_1_a import core
from sugarcode.modules.biofactory_1_a import boundary_ops as b

DAG = core.workflow_dag([{"op": "a"}, {"op": "b"}])
PROTO = core.generate_protocol("gibson", 2)
NAN = float("nan")


def deep_list(n=100_000):
    d = []
    for _ in range(n):
        d = [d]
    return d


def test_core_defects_documented():
    with pytest.raises(RecursionError):
        core.experiment_log(PROTO, deep_list())
    assert "NaN" in core.experiment_log(PROTO, {"x": NAN})["machine_readable"]
    with pytest.raises(IndexError):
        core.pid_control(1, [])
    with pytest.raises(ZeroDivisionError):
        core.pid_control(1, [0.5], dt=0)
    with pytest.raises(ZeroDivisionError):
        core.assay_quality([1], [1])
    with pytest.raises(ZeroDivisionError):
        core.assay_quality([1, 2], [1, 2])
    assert core.reroute_on_failure(DAG, 99, {"op": "x"})["failed_step"] == 99
    assert core.reroute_on_failure(DAG, 0, {"id": 5, "op": "x"})["fallback_id"] == 2


# ---- pid ----
def test_pid_matches_hand_oracle():
    # setpoint 1, measurements [0, 0.5], kp=.5 ki=.1 kd=.05 dt=1
    # k0: err=1 integ=1 ctrl=.5+.1+.05*1=.65 ; k1: err=.5 integ=1.5 ctrl=.25+.15+.05*(.5-1)=.375
    r = b.pid_control_checked(1, [0, 0.5])
    assert r["controls"] == pytest.approx([0.65, 0.375], abs=1e-12)
    assert r["final_error"] == 0.5 and r["integral_error"] == 1.5
    r = b.pid_control_checked(1, [0, 0.5], 1, 0, 0, 2)    # kp only
    assert r["controls"] == [1.0, 0.5] and r["integral_error"] == 3.0


@pytest.mark.parametrize("a", [
    dict(measurements=[]), dict(measurements="ab"), dict(measurements=None), dict(measurements={1: 1}),
    dict(measurements=[True]), dict(measurements=["1"]), dict(measurements=[NAN]), dict(measurements=[float("inf")]),
    dict(measurements=[1e7]), dict(measurements=[10**400]), dict(measurements=[[1]]), dict(measurements=[None]),
    dict(setpoint=True), dict(setpoint=NAN), dict(setpoint="1"), dict(setpoint=1e7), dict(setpoint=None), dict(setpoint=[1]),
    dict(dt=0), dict(dt=-1), dict(dt=NAN), dict(dt=1e-7), dict(dt=2e6), dict(dt=True), dict(dt="1"),
    dict(kp=-1), dict(kp=1001), dict(kp=NAN), dict(ki=True), dict(kd=None), dict(kp=[1]),
])
def test_pid_rejects(a):
    kw = dict(setpoint=1, measurements=[0.5])
    kw.update(a)
    with pytest.raises((TypeError, ValueError)):
        b.pid_control_checked(**kw)


def test_pid_caps_at_edges():
    assert len(b.pid_control_checked(1e6, [-1e6] * 10_000)["controls"]) == 10_000
    with pytest.raises(ValueError, match="measurements must have 1..10000 values"):
        b.pid_control_checked(1, [0.5] * 10_001)
    with pytest.raises(ValueError, match="measurements must have 1..10000 values"):
        b.pid_control_checked(1, [])
    b.pid_control_checked(1, [1e6])
    with pytest.raises(ValueError, match="measurements value must be between"):
        b.pid_control_checked(1, [1_000_000.001])
    b.pid_control_checked(1, [1], dt=1e-6)
    b.pid_control_checked(1, [1], dt=1e6)
    with pytest.raises(ValueError, match="dt must be between"):
        b.pid_control_checked(1, [1], dt=1.0000001e6)
    b.pid_control_checked(1, [1], kp=1000, ki=0, kd=1000)
    with pytest.raises(ValueError, match="kp must be between"):
        b.pid_control_checked(1, [1], kp=1000.001)
    with pytest.raises(TypeError, match="not bool"):
        b.pid_control_checked(1, [True])
    with pytest.raises(ValueError, match="must be finite"):
        b.pid_control_checked(1, [NAN])
    with pytest.raises(ValueError, match="magnitude too large"):
        b.pid_control_checked(1, [10**400])
    with pytest.raises(ValueError, match="magnitude too large"):
        b.pid_control_checked(1, [1e300])


# ---- assay ----
def test_assay_hand_oracle():
    # signal [10,12] mean 11 sd sqrt2 ; background [1,3] mean 2 sd sqrt2 ; z = 1-3*(2*sqrt2)/9
    r = b.assay_quality_checked([10, 12], [1, 3])
    assert r["z_prime"] == pytest.approx(1 - 3 * 2 * math.sqrt(2) / 9, abs=1e-12)
    assert r["signal_background"] == pytest.approx(5.5, abs=1e-12) and r["robust"] is False   # z = 0.057 <= 0.5


@pytest.mark.parametrize("sig,bg", [
    ([1], [1, 2]), ([1, 2], [1]), ([], [1, 2]), ([1, 2], []), ([1, 2], [1, 2]), ([5, 5], [5, 5]),
    ("ab", [1, 2]), ([1, 2], None), ([1, True], [1, 2]), ([1, NAN], [1, 2]), ([1, 2], [1, float("inf")]),
    ([1, 2e9], [1, 2]), ([1, "2"], [1, 2]), ([[1], [2]], [1, 2]), ([1, 10**400], [1, 2]), ({1, 2}, [1, 2]),
])
def test_assay_rejects(sig, bg):
    with pytest.raises((TypeError, ValueError)):
        b.assay_quality_checked(sig, bg)


def test_assay_edges_and_messages():
    b.assay_quality_checked([0, 2e9 / 2], [0, 1])
    b.assay_quality_checked([1e9, -1e9 + 1], [1, 2])
    with pytest.raises(ValueError, match="signal value must be between"):
        b.assay_quality_checked([1, 1_000_000_000.1], [1, 2])
    with pytest.raises(ValueError, match="signal must have 2..10000 values"):
        b.assay_quality_checked([1], [1, 2])
    with pytest.raises(ValueError, match="background must have 2..10000 values"):
        b.assay_quality_checked([1, 2], [1] * 10_001)
    with pytest.raises(ValueError, match="signal and background means are equal"):
        b.assay_quality_checked([1, 2], [2, 1])
    b.assay_quality_checked([1, 2], [1, 2.0000001])


# ---- dag / reroute ----
def test_workflow_dag_equal_core_and_rejects():
    s = [{"op": "a"}, {"op": "b"}, {"op": "c"}]
    assert b.workflow_dag_checked(s) == core.workflow_dag(s)
    assert b.workflow_dag_checked(tuple(s)) == core.workflow_dag(s)
    for bad in (5, None, "ab", {"a": 1}, [], ["a"], [1], [None]):
        with pytest.raises((TypeError, ValueError)):
            b.workflow_dag_checked(bad)
    assert len(b.workflow_dag_checked([{"op": "a"}] * 10_000)["nodes"]) == 10_000
    with pytest.raises(ValueError, match="steps must have 1..10000 entries"):
        b.workflow_dag_checked([{"op": "a"}] * 10_001)
    with pytest.raises(TypeError, match="step 1 must be a mapping"):
        b.workflow_dag_checked([{"op": "a"}, "b"])


def test_reroute_valid_equals_core():
    assert b.reroute_on_failure_checked(DAG, 0, {"op": "x"}) == core.reroute_on_failure(DAG, 0, {"op": "x"})
    assert b.reroute_on_failure_checked(DAG, 1, {"op": "x"})["fallback_id"] == 2


@pytest.mark.parametrize("dag,step,fb", [
    (None, 0, {"op": "x"}), ({}, 0, {"op": "x"}), ({"nodes": [], "edges": []}, 0, {"op": "x"}),
    ({"nodes": "ab", "edges": []}, 0, {"op": "x"}), ({"nodes": [{}], "edges": "ab"}, 0, {"op": "x"}),
    ({"nodes": [{}], "edges": [5]}, 0, {"op": "x"}), ({"nodes": [{}], "edges": [{}]}, 0, {"op": "x"}),
    (DAG, 99, {"op": "x"}), (DAG, -1, {"op": "x"}), (DAG, 2, {"op": "x"}), (DAG, True, {"op": "x"}),
    (DAG, 0.5, {"op": "x"}), (DAG, "0", {"op": "x"}), (DAG, None, {"op": "x"}), (DAG, [0], {"op": "x"}),
    (DAG, 0, [1]), (DAG, 0, None), (DAG, 0, "x"), (DAG, 0, {"id": 5}), (DAG, 0, {1: "a"}),
    (DAG, 0, {f"k{i}": 1 for i in range(51)}),
])
def test_reroute_rejects(dag, step, fb):
    with pytest.raises((TypeError, ValueError)):
        b.reroute_on_failure_checked(dag, step, fb)


def test_reroute_edges_and_messages():
    b.reroute_on_failure_checked(DAG, 1, {f"k{i}": 1 for i in range(50)})
    with pytest.raises(ValueError, match="fallback has more than 50 keys"):
        b.reroute_on_failure_checked(DAG, 1, {f"k{i}": 1 for i in range(51)})
    with pytest.raises(ValueError, match=r"failed_step must be in \[0, 1\]"):
        b.reroute_on_failure_checked(DAG, 2, {"op": "x"})
    with pytest.raises(ValueError, match="fallback must not set 'id'"):
        b.reroute_on_failure_checked(DAG, 0, {"id": 5})
    with pytest.raises(TypeError, match="failed_step must be an int"):
        b.reroute_on_failure_checked(DAG, True, {"op": "x"})
    big = {"nodes": [{}] * 10_000, "edges": []}
    b.reroute_on_failure_checked(big, 9_999, {"op": "x"})
    with pytest.raises(ValueError, match="dag must have 1..10000 nodes"):
        b.reroute_on_failure_checked({"nodes": [{}] * 10_001, "edges": []}, 0, {"op": "x"})
    with pytest.raises(ValueError, match="dag must have 1..10000 nodes"):
        b.reroute_on_failure_checked({"nodes": [{}], "edges": [{"source": 0}] * 10_001}, 0, {"op": "x"})


# ---- experiment log ----
def test_log_valid_equals_core_and_valid_json():
    res = {"od": [0.1, 0.2], "ok": True, "note": "fine", "n": 3, "none": None}
    r = b.experiment_log_checked(PROTO, res)
    assert r == core.experiment_log(PROTO, res)
    assert json.loads(r["machine_readable"]) == {"workflow": "gibson", "results": res}


def test_log_deep_100000_named_error_no_recursion():
    with pytest.raises(ValueError, match="nested deeper than 64"):
        b.experiment_log_checked(PROTO, deep_list())
    d = {}
    for _ in range(100_000):
        d = {"a": d}
    with pytest.raises(ValueError, match="nested deeper than 64"):
        b.experiment_log_checked(PROTO, d)


def test_log_depth_and_node_caps_pinned():
    ok = cur = []
    for _ in range(64):            # list at depth 64 is allowed
        nxt = []
        cur.append(nxt)
        cur = nxt
    b.experiment_log_checked(PROTO, ok)
    over = []
    cur = over
    for _ in range(65):
        nxt = []
        cur.append(nxt)
        cur = nxt
    with pytest.raises(ValueError, match="nested deeper than 64"):
        b.experiment_log_checked(PROTO, over)
    b.experiment_log_checked(PROTO, [0] * 99_999)                    # 1 + 99,999 = 100,000 nodes
    with pytest.raises(ValueError, match="more than 100000 values"):
        b.experiment_log_checked(PROTO, [0] * 100_000)               # 100,001 nodes


@pytest.mark.parametrize("res,exc", [
    ({"x": NAN}, ValueError), ({"x": float("inf")}, ValueError), ([float("-inf")], ValueError),
    ({"x": object()}, TypeError), ({"x"}, TypeError), ({1: "a"}, TypeError), ([b"x"], TypeError),
    ([10**400], ValueError), ([complex(1, 1)], TypeError),
])
def test_log_rejects_results(res, exc):
    with pytest.raises(exc):
        b.experiment_log_checked(PROTO, res)


@pytest.mark.parametrize("proto", [None, {}, {"workflow": 5}, [1], "x", {"workflow": None}])
def test_log_rejects_protocol(proto):
    with pytest.raises(TypeError, match="protocol must be a mapping with a text workflow"):
        b.experiment_log_checked(proto, [1])


def test_guard_messages_pinned():
    with pytest.raises(TypeError, match="setpoint must be a number$"):
        b.pid_control_checked("1", [0.5])
    with pytest.raises(TypeError, match="measurements value must be a number$"):
        b.pid_control_checked(1, [None])
    with pytest.raises(TypeError, match="steps must be a list or tuple of mappings"):
        b.workflow_dag_checked(5)
    with pytest.raises(TypeError, match="steps must be a list or tuple of mappings"):
        b.workflow_dag_checked("ab")
    with pytest.raises(TypeError, match="fallback must be a mapping"):
        b.reroute_on_failure_checked(DAG, 0, "x")
    with pytest.raises(TypeError, match="fallback must be a mapping"):
        b.reroute_on_failure_checked(DAG, 0, [("a", 1)])
