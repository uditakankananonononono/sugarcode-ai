import copy
import math
import pytest

from sugarcode.modules.biofactory_1_a import core
from sugarcode.modules.biofactory_1_a import boundary_report as b

NAN = float("nan")


def test_core_defects_documented():
    with pytest.raises(TypeError, match="unhashable"):
        core.dbtl_report(["x"])
    assert core.dbtl_report("gibson", 0)["protocol"]["plates"] == 0
    assert core.dbtl_report("gibson", observations=())["condition_update"]["posterior_mean"] == pytest.approx(0.7)
    assert math.isnan(core.dbtl_report("gibson", observations=(NAN,))["condition_update"]["posterior_mean"])
    with pytest.raises(ZeroDivisionError):
        core.dbtl_report("gibson", assay_signal=(1,))
    with pytest.raises(ZeroDivisionError):
        core.dbtl_report("gibson", assay_signal=(1, 2), assay_background=(1, 2))
    with pytest.raises(KeyError):
        core.factory_diagnostics({})
    with pytest.raises(TypeError):
        core.factory_diagnostics(None)


def test_dbtl_valid_equals_core_and_hand_oracle():
    r = b.dbtl_report_checked("gibson")
    assert r == core.dbtl_report("gibson")
    # posterior: precision = 1/.1 + 3/.05 = 70 ; mean = (.7/.1 + 2.3/.05)/70 = 53/70
    assert r["condition_update"]["posterior_mean"] == pytest.approx(53 / 70, abs=1e-12)
    assert r["condition_update"]["posterior_variance"] == pytest.approx(1 / 70, abs=1e-12)
    assert b.dbtl_report_checked("golden_gate", 96)["protocol"]["plates"] == 1
    assert b.dbtl_report_checked("golden_gate", 97)["protocol"]["plates"] == 2


@pytest.mark.parametrize("kw", [
    dict(workflow=["x"]), dict(workflow={"a": 1}), dict(workflow=None), dict(workflow=5), dict(workflow=True),
    dict(n_constructs=0), dict(n_constructs=-1), dict(n_constructs=100_001), dict(n_constructs=10**9),
    dict(n_constructs=True), dict(n_constructs=2.5), dict(n_constructs="8"), dict(n_constructs=None), dict(n_constructs=10**400),
    dict(observations=()), dict(observations=[]), dict(observations="abc"), dict(observations=None),
    dict(observations=(NAN,)), dict(observations=(True,)), dict(observations=("1",)), dict(observations=(1e7,)),
    dict(observations=(0.5,) * 1001), dict(observations=({1: 1},)),
    dict(assay_signal=(1,)), dict(assay_signal=()), dict(assay_signal=(1, NAN)), dict(assay_signal=(1, True)),
    dict(assay_signal=(1, 2), assay_background=(1, 2)), dict(assay_background=(1,)), dict(assay_background=None),
    dict(assay_signal=(1.0,) * 1001),
])
def test_dbtl_rejects(kw):
    a = dict(workflow="gibson")
    a.update(kw)
    with pytest.raises((TypeError, ValueError)):
        b.dbtl_report_checked(**a)


def test_dbtl_unknown_workflow_keeps_keyerror():
    with pytest.raises(KeyError, match="unknown workflow 'nope'"):
        b.dbtl_report_checked("nope")


def test_dbtl_caps_at_edges_and_messages():
    assert b.dbtl_report_checked("gibson", 100_000)["protocol"]["n_constructs"] == 100_000
    assert b.dbtl_report_checked("gibson", 1)["protocol"]["plates"] == 1
    with pytest.raises(ValueError, match=r"n_constructs must be in \[1, 100000\]"):
        b.dbtl_report_checked("gibson", 100_001)
    with pytest.raises(ValueError, match=r"n_constructs must be in \[1, 100000\]"):
        b.dbtl_report_checked("gibson", 0)
    b.dbtl_report_checked("gibson", observations=(0.5,) * 1000)
    with pytest.raises(ValueError, match="observations must have at most 1000 values"):
        b.dbtl_report_checked("gibson", observations=(0.5,) * 1001)
    with pytest.raises(ValueError, match="observations must have 1..10000 values"):
        b.dbtl_report_checked("gibson", observations=())
    b.dbtl_report_checked("gibson", assay_signal=(1.0, 3.0) * 500, assay_background=(0.0, 1.0))
    with pytest.raises(ValueError, match="assay series must have at most 1000 values"):
        b.dbtl_report_checked("gibson", assay_signal=(1.0, 3.0) * 500 + (2.0,))
    with pytest.raises(ValueError, match="assay series must have at most 1000 values"):
        b.dbtl_report_checked("gibson", assay_background=(0.0, 1.0) * 500 + (2.0,))
    with pytest.raises(ValueError, match="signal and background means are equal"):
        b.dbtl_report_checked("gibson", assay_signal=(1, 2), assay_background=(2, 1))
    with pytest.raises(TypeError, match="workflow must be text"):
        b.dbtl_report_checked(["x"])
    with pytest.raises(TypeError, match="n_constructs must be an int"):
        b.dbtl_report_checked("gibson", 2.5)


REPORT = core.dbtl_report("gibson")


def test_diagnostics_equals_core_and_hand_oracle():
    r = b.factory_diagnostics_checked(REPORT)
    assert r == core.factory_diagnostics(REPORT)
    assert r["construct_count"] == 8.0 and r["plate_count"] == 1.0
    assert r["posterior_mean"] == pytest.approx(53 / 70, abs=1e-12)


def _mut(path, value):
    r = copy.deepcopy(REPORT)
    cur = r
    for k in path[:-1]:
        cur = cur[k]
    if value is KeyError:
        del cur[path[-1]]
    else:
        cur[path[-1]] = value
    return r


@pytest.mark.parametrize("bad", [None, [], "x", 5, {}, {"protocol": 1}])
def test_diagnostics_rejects_shape(bad):
    with pytest.raises((TypeError,)):
        b.factory_diagnostics_checked(bad)


@pytest.mark.parametrize("path", [("protocol",), ("dag",), ("schedule",), ("condition_update",), ("assay_quality",),
                                   ("protocol", "plates"), ("protocol", "steps"), ("dag", "edges"),
                                   ("schedule", "makespan_min"), ("assay_quality", "z_prime")])
def test_diagnostics_missing_key(path):
    with pytest.raises(TypeError):
        b.factory_diagnostics_checked(_mut(path, KeyError))


@pytest.mark.parametrize("path,val,exc", [
    (("protocol", "n_constructs"), True, TypeError), (("protocol", "plates"), NAN, ValueError),
    (("protocol", "estimated_runtime_min"), "5", TypeError), (("protocol", "steps"), "ab", TypeError),
    (("protocol", "equipment_required"), 5, TypeError), (("dag", "nodes"), None, TypeError),
    (("schedule", "makespan_min"), float("inf"), ValueError), (("schedule", "makespan_min"), -1, ValueError),
    (("condition_update", "posterior_mean"), NAN, ValueError), (("condition_update", "posterior_variance"), [1], TypeError),
    (("assay_quality", "z_prime"), None, TypeError), (("assay_quality", "signal_background"), 10**400, ValueError),
    (("protocol",), [1], TypeError), (("dag",), "x", TypeError),
])
def test_diagnostics_rejects_values(path, val, exc):
    with pytest.raises(exc):
        b.factory_diagnostics_checked(_mut(path, val))


def test_diagnostics_negative_bounds_and_edges():
    b.factory_diagnostics_checked(_mut(("schedule", "makespan_min"), 0))
    b.factory_diagnostics_checked(_mut(("condition_update", "posterior_mean"), -1e15))
    with pytest.raises(ValueError, match="magnitude too large"):
        b.factory_diagnostics_checked(_mut(("condition_update", "posterior_mean"), -1e15 * 1.0000001))
    with pytest.raises(ValueError, match="magnitude too large"):
        b.factory_diagnostics_checked(_mut(("assay_quality", "z_prime"), 10**15 + 1))
    with pytest.raises(TypeError, match="protocol steps must be a list"):
        b.factory_diagnostics_checked(_mut(("protocol", "steps"), "ab"))
    with pytest.raises(TypeError, match="report must be a mapping$"):
        b.factory_diagnostics_checked([1])
    with pytest.raises(TypeError, match="report must be a mapping with dag"):
        b.factory_diagnostics_checked(_mut(("dag",), KeyError))
