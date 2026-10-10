"""H23 authored NOT RUN: controlled cutoff policy, not physical validation.

Oracle: accepted builder-generated exact Decimal arithmetic, not ProDy.
No product changes. Current strict '<' characterization only; ProDy pending.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from sugarcode.modules.evofold_4d.core import _kirchhoff

FIXTURE = Path(__file__).parent / "fixtures" / "h23_boundaries" / "decimal_oracle.json"
SHA256 = "05d4f7b3a8a08e6f7b6950d9ff17110720ae051a166134ed3281d7e00395c656"


@pytest.fixture(scope="module")
def frozen():
    raw = FIXTURE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SHA256
    return json.loads(raw)


@pytest.mark.parametrize("label", ["below", "exact", "above"])
def test_existing_kirchhoff_cutoff_policy_matches_frozen_decimal(label, frozen):
    record = next(row for row in frozen["distances"] if row["label"] == label)
    # Frozen integer coordinates are exactly representable binary64; expected
    # membership is a frozen Decimal boolean, not computed from product norm.
    coords = np.array(record["coordinates_decimal"], dtype=float)
    matrix = _kirchhoff(coords, cutoff=10.0)
    admitted = record["strict_less_than_10"]
    assert matrix.shape == (2, 2)
    assert bool(matrix[0, 1] != 0) is admitted
    assert bool(matrix[1, 0] != 0) is admitted
    assert bool(matrix[0, 0] != 0) is admitted
    assert bool(matrix[1, 1] != 0) is admitted
    if label == "exact":
        assert record["less_than_or_equal_10"] is True and admitted is False
