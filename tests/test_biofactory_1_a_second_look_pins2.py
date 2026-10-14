"""Unit 31 v2 pins (tests only for behaviour, PARTIAL) closing the gaps found by an independent second grade:
assay series bounds (+-1e9), observation range (+-1e6), minimum replicates (2), series length 1000 inclusive,
diagnostics zero values, and the guard ORDER (length caps before any value scan; node cap before queueing children).
Expected values are hand-derived literals from the stated limits. Caps are this module's choices, not spec values.
Toy engineering arithmetic only."""
import pytest
from sugarcode.modules.biofactory_1_a import boundary_ops as b, boundary_report as r


def err(exc, fn, *a, **k):
    with pytest.raises(exc) as e:
        fn(*a, **k)
    return str(e.value)


def test_pid_hand_values():
    # setpoint 2, measurements [0,1], kp=ki=kd=1, dt=2: errors 2,1; integral 4 then 6; derivative (1-2)/2=-0.5 then ...
    out = b.pid_control_checked(2, [0, 1], kp=1, ki=1, kd=1, dt=2)
    assert out == dict(controls=[7.0, 6.5], final_error=1.0, integral_error=6.0)


def test_ops_assay_bounds_both_series_both_sides():
    ok = [1e9, -1e9]
    assert isinstance(b.assay_quality_checked(ok, [0, 1]), dict)
    assert isinstance(b.assay_quality_checked([0, 1], ok), dict)
    for bad in ([1e9 + 1, 0], [-1e9 - 1, 0]):
        assert err(ValueError, b.assay_quality_checked, bad, [0, 1]) == "signal value must be between -1e+09 and 1e+09"
        assert err(ValueError, b.assay_quality_checked, [0, 1], bad) == "background value must be between -1e+09 and 1e+09"


def test_ops_assay_min_replicates_two():
    assert err(ValueError, b.assay_quality_checked, [1], [0, 1]) == "signal must have 2..10000 values"
    assert err(ValueError, b.assay_quality_checked, [0, 1], [1]) == "background must have 2..10000 values"


def test_report_observation_range_exact():
    r.dbtl_report_checked("gibson", observations=[1e6])
    r.dbtl_report_checked("gibson", observations=[-1e6])
    for bad in (1e6 + 1, -1e6 - 1):
        assert err(ValueError, r.dbtl_report_checked, "gibson", observations=[bad]) == "observations value must be between -1e+06 and 1e+06"
    assert r.MAX_VALUE == 1e6


@pytest.mark.parametrize("key", ["assay_signal", "assay_background"])
def test_report_assay_range_1e9_exact(key):
    other = {"assay_signal": "assay_background", "assay_background": "assay_signal"}[key]
    base = {other: [5, 6]}
    r.dbtl_report_checked("gibson", **{key: [1e9, 0]}, **base)
    r.dbtl_report_checked("gibson", **{key: [-1e9, 0]}, **base)
    for bad in (1e9 + 1, -1e9 - 1):
        assert err(ValueError, r.dbtl_report_checked, "gibson", **{key: [bad, 0]}, **base) == f"{key} value must be between -1e+09 and 1e+09"


@pytest.mark.parametrize("key", ["assay_signal", "assay_background"])
def test_report_assay_min_replicates_two(key):
    other = {"assay_signal": [5, 6], "assay_background": [0, 1]}
    other.pop(key)
    assert err(ValueError, r.dbtl_report_checked, "gibson", **{key: [1]}, **other) == f"{key} must have 2..10000 values"
    assert err(ValueError, r.dbtl_report_checked, "gibson", **{key: []}, **other) == f"{key} must have 2..10000 values"


def test_report_series_length_1000_inclusive():
    r.dbtl_report_checked("gibson", observations=[0.5] * 1000)
    r.dbtl_report_checked("gibson", assay_background=[0, 1] * 500)
    r.dbtl_report_checked("gibson", assay_signal=[5, 6] * 500, assay_background=[0, 1])
    assert err(ValueError, r.dbtl_report_checked, "gibson", observations=[0.5] * 1001) == "observations must have at most 1000 values"
    assert err(ValueError, r.dbtl_report_checked, "gibson", assay_background=[0, 1] * 500 + [0]) == "assay series must have at most 1000 values"
    assert err(ValueError, r.dbtl_report_checked, "gibson", assay_signal=[5, 6] * 500 + [5]) == "assay series must have at most 1000 values"


def test_guard_order_length_cap_before_value_scan():
    # an over-long series whose values are all invalid text: the length refusal must come first (no scan)
    assert err(ValueError, r.dbtl_report_checked, "gibson", observations=["x"] * 1001) == "observations must have at most 1000 values"
    assert err(ValueError, r.dbtl_report_checked, "gibson", assay_signal=["x"] * 1001) == "assay series must have at most 1000 values"
    assert err(ValueError, r.dbtl_report_checked, "gibson", assay_background=["x"] * 1001) == "assay series must have at most 1000 values"
    # within the cap, an invalid value is reported as a type error
    assert err(TypeError, r.dbtl_report_checked, "gibson", observations=["x"]) == "observations value must be a number"


def test_guard_order_node_cap_before_children_queued():
    proto = {"workflow": "gibson"}
    # root + 99_999 children = 100_000 nodes: accepted; one more refused. The refusal must precede visiting children:
    # the last child is an unsupported object, which would raise TypeError if children were visited first.
    assert err(ValueError, b.experiment_log_checked, proto, [0] * 100_000 + [object()]) == "results has more than 100000 values"
    assert err(ValueError, b.experiment_log_checked, proto, {str(i): 0 for i in range(100_000)} | {"z": object()}) == "results has more than 100000 values"
    assert len(b.experiment_log_checked(proto, [0] * 99_999)["results"]) == 99_999
    assert err(TypeError, b.experiment_log_checked, proto, [0, object()]).startswith("results contains unsupported type")


def _rep():
    return r.dbtl_report_checked("gibson")


@pytest.mark.parametrize("path", [("protocol", "n_constructs"), ("protocol", "plates"), ("protocol", "estimated_runtime_min"),
                                  ("schedule", "makespan_min")])
def test_diagnostics_zero_accepted_negative_refused(path):
    rep = _rep(); rep[path[0]][path[1]] = 0
    out = r.factory_diagnostics_checked(rep)
    assert isinstance(out, dict)
    rep = _rep(); rep[path[0]][path[1]] = -1
    label = f"{path[0]} {path[1]}"
    assert err(ValueError, r.factory_diagnostics_checked, rep) == f"{label} must be between 0 and 1e+15"


def test_diagnostics_zero_values_reach_outputs():
    rep = _rep(); rep["protocol"]["n_constructs"] = 0
    assert r.factory_diagnostics_checked(rep)["construct_count"] == 0
    rep = _rep(); rep["schedule"]["makespan_min"] = 0
    assert r.factory_diagnostics_checked(rep)["makespan"] == 0


def test_guard_counts_pending_siblings():
    # root = [[0]*10, A] with A = 99_997 zeros + an unsupported object: total nodes 1 + 2 + 10 + 99_998 = 100_011 > cap.
    # The pending sibling and A's own children are both counted before A's children are queued, so the refusal
    # (ValueError) precedes visiting the object (TypeError).
    proto = {"workflow": "gibson"}
    a = [0] * 99_997 + [object()]
    assert err(ValueError, b.experiment_log_checked, proto, [[0] * 10, a]) == "results has more than 100000 values"


def test_pid_dt_lower_bound_exact():
    assert isinstance(b.pid_control_checked(1, [0], dt=1e-6), dict)
    assert err(ValueError, b.pid_control_checked, 1, [0], dt=9e-7) == "dt must be between 1e-06 and 1e+06"
    assert isinstance(b.pid_control_checked(1, [0], dt=1e6), dict)
    assert err(ValueError, b.pid_control_checked, 1, [0], dt=1e6 + 1) == "dt must be between 1e-06 and 1e+06"
