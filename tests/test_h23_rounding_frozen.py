"""H23 authored NOT RUN: controlled real-path formatting, not solver validation.

Only existing dependency names are patched, restored per test. Frozen expectations
are accepted builder-generated Decimal half-even records, never product output.
Negative 4dp records are arithmetic-only, excluded from physical RMSD path tests.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from sugarcode.modules.evofold_4d import core

FIXTURE = Path(__file__).parent / "fixtures" / "h23_boundaries" / "decimal_oracle.json"
SHA256 = "05d4f7b3a8a08e6f7b6950d9ff17110720ae051a166134ed3281d7e00395c656"


@pytest.fixture(scope="module")
def frozen():
    raw = FIXTURE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SHA256
    return json.loads(raw)


def _zero_displacement_eigh(hessian):
    # Deliberately controlled dependency response, NOT an orthonormal eigensolve.
    # A positive eigenvalue gets the real path past non-rigid selection, but its
    # zero displacement column leaves every real constructed frame equal to C0.
    size = hessian.shape[0]
    values = np.zeros(size)
    values[-1] = 1.0
    vectors = np.zeros((size, size))
    return values, vectors


@pytest.mark.parametrize("parity", ["even", "odd"])
@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("side", ["below", "tie", "above"])
def test_real_frame_rounding_frozen_half_even_both_sides(parity, sign, side, frozen, monkeypatch):
    record = next(row for row in frozen["rounding"] if row["precision"] == 3
                  and row["retained_digit_parity_at_tie"] == parity
                  and row["sign"] == sign and row["side_in_numeric_order"] == side)
    raw = float(record["raw_exact_decimal"])
    expected = float(record["expected_half_even_decimal"])
    # Controlled raw coords include both sign/tie/boundary sides; no expected
    # values are obtained via float-round, product or solver.
    coords = [[raw, 0.0, 0.0], [raw, 0.0, 0.0]]
    original_anm = core.anm_modes
    original_eigh = np.linalg.eigh
    with monkeypatch.context() as patch:
        patch.setattr(core, "anm_modes", lambda *a, **kw: {})
        patch.setattr(np.linalg, "eigh", _zero_displacement_eigh)
        result = core.transition_trace(coords, steps=2)
    assert core.anm_modes is original_anm and np.linalg.eigh is original_eigh
    assert len(result["frames"]) == 2
    for frame in result["frames"]:
        for row in frame:
            assert abs(row[0] - expected) <= 1e-12
            assert row[1:] == [0.0, 0.0]


@pytest.mark.parametrize("parity", ["even", "odd"])
@pytest.mark.parametrize("side", ["below", "tie", "above"])
def test_real_nonnegative_rmsd_rounding_and_max_frozen(parity, side, frozen, monkeypatch):
    record = next(row for row in frozen["rounding"] if row["precision"] == 4
                  and row["retained_digit_parity_at_tie"] == parity
                  and row["sign"] == 1 and row["side_in_numeric_order"] == side)
    raw = float(record["raw_exact_decimal"])
    expected = float(record["expected_half_even_decimal"])
    original_anm = core.anm_modes
    original_eigh = np.linalg.eigh
    original_sqrt = np.sqrt
    calls = []
    def controlled_sqrt(value):
        # Only the existing sqrt lookup is injected. Norm/eigh are not claimed
        # independent numerical results. Actual product rounding/max remain real.
        calls.append(value)
        return raw
    with monkeypatch.context() as patch:
        patch.setattr(core, "anm_modes", lambda *a, **kw: {})
        patch.setattr(np.linalg, "eigh", _zero_displacement_eigh)
        patch.setattr(np, "sqrt", controlled_sqrt)
        result = core.transition_trace([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], steps=2)
    assert core.anm_modes is original_anm and np.linalg.eigh is original_eigh
    assert np.sqrt is original_sqrt
    assert calls
    assert len(result["rmsd_trace"]) == 2
    assert all(abs(value - expected) <= 1e-12 for value in result["rmsd_trace"])
    assert abs(result["max_rmsd"] - expected) <= 1e-12
