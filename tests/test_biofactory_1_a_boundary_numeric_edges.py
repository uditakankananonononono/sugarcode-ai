"""Numeric-edge pins for biofactory_1_a boundary_ops/boundary_report (PARTIAL).
Reproduction: assay_quality_checked([np.float64(10), 12], [1, 3])["robust"] is np.bool_,
which json.dumps cannot serialise, while the same call with python floats gives bool."""
import json
import numpy as np
from sugarcode.modules.biofactory_1_a import boundary_ops as b, boundary_report as r


def test_assay_quality_numpy_float_gives_json_serialisable_result():
    a = b.assay_quality_checked([np.float64(10), 12], [1, np.float64(3)])
    p = b.assay_quality_checked([10.0, 12.0], [1.0, 3.0])
    assert type(a["robust"]) is bool
    assert json.dumps(a, sort_keys=True) == json.dumps(p, sort_keys=True)


def test_dbtl_report_numpy_float_equals_python_float():
    a = r.dbtl_report_checked("golden_gate", 8, [np.float64(0.6), 0.8], [np.float64(10), 11], [1, np.float64(1.2)])
    p = r.dbtl_report_checked("golden_gate", 8, [0.6, 0.8], [10.0, 11], [1, 1.2])
    assert json.dumps(a, sort_keys=True) == json.dumps(p, sort_keys=True)


def test_pid_numpy_scalars_become_python_floats():
    out = b.pid_control_checked(np.float64(1), [np.float64(0), 0.5], np.float64(.5), .1, .05, np.float64(1))
    assert all(type(x) is float for x in out["controls"])
    assert out == b.pid_control_checked(1, [0, 0.5], .5, .1, .05, 1)
