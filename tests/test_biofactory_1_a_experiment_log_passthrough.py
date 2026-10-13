"""Documents (does not endorse) how experiment_log_checked treats -0.0 and numpy floats (PARTIAL).

Parent ruling: leave verbatim, pin with a test. Expected values are hand-derived literals:
json.dumps(-0.0) == '-0.0'; np.float64 subclasses float so it is accepted and passed through
unchanged (same object); np.float32 is not a float subclass so it is refused."""
import json
import numpy as np
import pytest

from sugarcode.modules.biofactory_1_a import core
from sugarcode.modules.biofactory_1_a import boundary_ops as b

PROTO = core.generate_protocol("gibson", 2)


def test_negative_zero_passes_through_and_serialises_as_minus_zero():
    r = b.experiment_log_checked(PROTO, {"x": -0.0})
    assert r["machine_readable"] == json.dumps({"workflow": PROTO["workflow"], "results": {"x": -0.0}}, sort_keys=True)
    assert '"x": -0.0' in r["machine_readable"]
    assert str(r["results"]["x"]) == "-0.0"          # sign of zero preserved, not normalised to 0.0


def test_numpy_float64_is_accepted_and_returned_as_the_same_object():
    v = np.float64(1.5)
    r = b.experiment_log_checked(PROTO, {"x": v})
    assert r["results"]["x"] is v
    assert '"x": 1.5' in r["machine_readable"]


def test_numpy_float64_negative_zero_keeps_its_sign():
    r = b.experiment_log_checked(PROTO, [np.float64(-0.0)])
    assert '"results": [-0.0]' in r["machine_readable"]


def test_numpy_float64_nonfinite_is_still_refused():
    for bad in (np.float64("nan"), np.float64("inf"), np.float64("-inf")):
        with pytest.raises(ValueError, match="results must be finite"):
            b.experiment_log_checked(PROTO, {"x": bad})


def test_numpy_float32_and_int64_are_refused_as_unsupported_types():
    for bad in (np.float32(1.5), np.int64(3)):
        with pytest.raises(TypeError, match="unsupported type"):
            b.experiment_log_checked(PROTO, {"x": bad})
