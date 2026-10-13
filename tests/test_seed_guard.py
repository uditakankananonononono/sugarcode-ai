import re

import pytest

from sugarcode.modules.stability_ai import core as score, seed_guard as sg
from sugarcode.modules.syndroid import core as ycore, seed_guard as yg

CAP = 2**32 - 1
STAB = {"mode": "plasmid", "burden": 0.1, "size_kb": 5}


def msg(s):
    return re.escape(s) + "$"


@pytest.mark.parametrize("g", [sg.check_seed, yg.check_seed])
def test_check_seed_pins(g):
    assert g(0) == 0 and g(CAP) == CAP
    for bad in (True, False, 1.0, "1", None, [1], [[]], 1 + 0j):
        with pytest.raises(TypeError, match=msg("seed must be an integer")):
            g(bad)
    for bad in (-1, CAP + 1, 2**64, -(2**64), 10**400):
        with pytest.raises(ValueError, match=msg(f"seed must be between 0 and {CAP}")):
            g(bad)


def test_cap_applies_through_every_wrapped_function():
    for fn in (sg.stochastic_drift, sg.stochastic_drift_v2, sg.analyze_stability, sg.analyze_stability_v2):
        with pytest.raises(ValueError, match=msg(f"seed must be between 0 and {CAP}")):
            fn(STAB, seed=CAP + 1)
        with pytest.raises(ValueError, match=msg(f"seed must be between 0 and {CAP}")):
            fn(STAB, seed=-1)
        with pytest.raises(TypeError, match=msg("seed must be an integer")):
            fn(STAB, seed=True)
    for fn in (yg.mechanistic_cell_program, yg.design_syndroid):
        with pytest.raises(ValueError, match=msg(f"seed must be between 0 and {CAP}")):
            fn(seed=CAP + 1)
        with pytest.raises(ValueError, match=msg(f"seed must be between 0 and {CAP}")):
            fn(seed=-1)
        with pytest.raises(TypeError, match=msg("seed must be an integer")):
            fn(seed=True)


def test_valid_seed_results_equal_core_called_directly():
    kw = dict(generations=5, population=50, replicates=4)
    assert sg.stochastic_drift(STAB, seed=CAP, **kw) == score.stochastic_drift(STAB, seed=CAP, **kw)
    assert sg.stochastic_drift(STAB, seed=0, **kw) == score.stochastic_drift(STAB, seed=0, **kw)
    assert sg.stochastic_drift(STAB, **kw) == score.stochastic_drift(STAB, **kw)
    assert yg.design_syndroid(hours=1, seed=7) == ycore.design_syndroid(hours=1, seed=7)
    assert yg.design_syndroid(hours=1) == ycore.design_syndroid(hours=1)
    assert yg.mechanistic_cell_program(None, hours=1, seed=CAP) == ycore.mechanistic_cell_program(None, hours=1, seed=CAP)


def test_core_errors_pass_through_unchanged():
    with pytest.raises(ValueError, match=msg("burden must be in [0, 1]")):
        sg.stochastic_drift({"mode": "plasmid", "burden": 5, "size_kb": 5}, seed=1)
