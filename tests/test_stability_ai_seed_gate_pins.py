"""Behavior pins for stability_ai.seed_gate (stochastic_drift, stochastic_drift_v2), moved from the removed seed_guard cases.

Exact messages, 0..2**63-1 boundaries at N and N+1, valid-seed equality with core, core errors passing through, numpy ints.
"""
import re

import numpy as np
import pytest

from sugarcode.modules.stability_ai import core, seed_gate as gate

CAP = 2**63 - 1
STAB = {"mode": "plasmid", "burden": 0.1, "size_kb": 5}
KW = dict(generations=5, population=50, replicates=4)
NAMES = ["stochastic_drift", "stochastic_drift_v2"]


def msg(s):
    return re.escape(s) + "$"


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, [1], [[]], 1 + 0j, np.float64(1.0), np.bool_(True)])
def test_wrong_type_message(name, bad):
    with pytest.raises(TypeError, match=msg("seed must be an integer")):
        getattr(gate, name)(STAB, seed=bad, **KW)


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("bad", [-1, CAP + 1, 2**64, -(2**64), 10**400, np.int64(-1)])
def test_out_of_range_message(name, bad):
    with pytest.raises(ValueError, match=msg(f"seed must be between 0 and {CAP}")):
        getattr(gate, name)(STAB, seed=bad, **KW)


@pytest.mark.parametrize("name", NAMES)
def test_valid_seed_results_equal_core(name):
    g, c = getattr(gate, name), getattr(core, name)
    for s in (0, 1, 2**32 - 1, 2**32, 2**40, CAP):
        assert g(STAB, seed=s, **KW) == c(STAB, seed=s, **KW)
    assert g(STAB, **KW) == c(STAB, **KW)
    for s in (np.int64(9), np.uint32(9), np.uint64(CAP)):
        assert g(STAB, seed=s, **KW) == c(STAB, seed=int(s), **KW)


@pytest.mark.parametrize("name", NAMES)
def test_core_errors_pass_through_unchanged(name):
    with pytest.raises(ValueError, match=msg("burden must be in [0, 1]")):
        getattr(gate, name)({"mode": "plasmid", "burden": 5, "size_kb": 5}, seed=1)
