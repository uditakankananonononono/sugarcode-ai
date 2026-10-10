"""H24 authored NOT RUN: real-path aggregation with frozen variable inputs.

Controlled dependency response, not solver/physical RMSD validation. Only
existing anm_modes/eigh/sqrt names patched; serial per-process execution required.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from sugarcode.modules.evofold_4d import core

FIXTURE = Path(__file__).parent / "fixtures" / "h24_aggregation" / "decimal_oracle.json"
SHA256 = "39750d4e4d25fedd9e2f7732966d0f7d6d926d8cffef90fd981e8bb17a5ceb9f"


@pytest.fixture(scope="module")
def frozen():
    raw = FIXTURE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SHA256
    return json.loads(raw)


def _zero_displacement_eigh(hessian):
    size = hessian.shape[0]
    values = np.zeros(size)
    values[-1] = 1.0
    return values, np.zeros((size, size))


@pytest.mark.parametrize("case_name", ["interior_max", "interior_min"])
def test_real_varying_rmsd_trace_and_max_match_frozen_aggregates(case_name, frozen, monkeypatch):
    record = frozen if case_name == "interior_max" else frozen["second_case"]
    raw_sequence = tuple(float(value) for value in record["raw_nonnegative_rmsd_inputs"])
    expected_trace = tuple(float(value) for value in record["rounded4_rmsd_trace"])
    expected_max = float(record["rounded_trace_aggregates"]["max"])
    # Expected values are literals from pre-test Decimal freeze, never computed
    # by float-round, product output or max(actual trace).
    assert len(raw_sequence) == len(expected_trace) == 4
    responses = iter(raw_sequence)
    sqrt_arguments = []
    original_anm, original_eigh, original_sqrt = core.anm_modes, np.linalg.eigh, np.sqrt
    def controlled_sqrt(value):
        sqrt_arguments.append(value)
        return next(responses)  # Extra calls fail instead of silently cycling.
    with monkeypatch.context() as patch:
        patch.setattr(core, "anm_modes", lambda *a, **kw: {})
        patch.setattr(np.linalg, "eigh", _zero_displacement_eigh)
        patch.setattr(np, "sqrt", controlled_sqrt)
        result = core.transition_trace([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], steps=4)
    assert core.anm_modes is original_anm and np.linalg.eigh is original_eigh
    assert np.sqrt is original_sqrt
    assert len(sqrt_arguments) == 4
    with pytest.raises(StopIteration):
        next(responses)
    assert len(result["rmsd_trace"]) == 4
    for got, expected in zip(result["rmsd_trace"], expected_trace):
        assert abs(got - expected) <= 1e-12
    assert abs(result["max_rmsd"] - expected_max) <= 1e-12
    # First case explicitly distinguishes max from all frozen wrong aggregates;
    # second is the complementary ordered trace with an interior minimum.
    if case_name == "interior_max":
        for name in ("min", "first", "last", "mean", "sum"):
            assert abs(result["max_rmsd"] - float(record["rounded_trace_aggregates"][name])) > 1e-12
