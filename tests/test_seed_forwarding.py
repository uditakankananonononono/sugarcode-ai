"""Every seed wrapper hands core a plain Python int, and every public wrapper really wraps the core function."""
import importlib

import numpy as np
import pytest

from sugarcode.seed_check import MAX_SEED, check_seed

WRAPPERS = {
    "bioprint_pro.seed_checked": ["oldroyd_b_extrusion", "optimize_print"],
    "biosimvr.seed_checked": ["simulate_protocol", "molecular_docking_experiment", "run_experiment"],
    "cellfatenet.seed_checked": ["identify_attractors", "stochastic_validate", "simulate_fate"],
    "dti_bench.seed_checked": ["validate_dti"],
    "evofold_4d.seed_checked": ["langevin_dynamics", "dynamics_report"],
    "liquid_biopsy.seed_checked": ["bootstrap_haplotype_weights", "fragment_length_model"],
    "living_computer.seed_checked": ["stochastic_simulate", "monte_carlo_robustness"],
    "syndroid.seed_checked": ["stochastic_gene_expression", "evolutionary_stability"],
    "syndroid.seed_guard": ["mechanistic_cell_program", "design_syndroid"],
    "stability_ai.seed_guard": ["stochastic_drift", "stochastic_drift_v2", "analyze_stability", "analyze_stability_v2"],
}
MODS = sorted(WRAPPERS)


def mod(name):
    return importlib.import_module("sugarcode.modules." + name)


def spy_factory():
    seen = []

    def spy(x, *, seed=1):
        seen.append(seed)
        return "ok"

    return spy, seen


@pytest.mark.parametrize("name", MODS)
@pytest.mark.parametrize("raw", [np.int64(5), np.uint8(7), np.uint64(9), np.uint64(MAX_SEED), 5, np.int64(MAX_SEED)])
def test_core_receives_plain_int(name, raw):
    spy, seen = spy_factory()
    assert mod(name)._guard(spy)(0, seed=raw) == "ok"
    assert type(seen[0]) is int and seen[0] == int(raw)


@pytest.mark.parametrize("name", MODS)
def test_positional_and_default_seed_paths(name):
    spy, seen = spy_factory()
    g = mod(name)._guard(spy)
    g(0, seed=np.int32(3))
    g(0)  # seed not given: default untouched
    assert type(seen[0]) is int and seen[1] == 1


@pytest.mark.parametrize("name", MODS)
def test_none_seed_is_refused_by_every_wrapper(name):
    spy, seen = spy_factory()
    with pytest.raises(TypeError, match=r"^seed must be an integer$"):
        mod(name)._guard(spy)(0, seed=None)
    assert seen == []


def test_uint64_plus_one_is_not_float_in_core():
    spy, seen = spy_factory()
    mod("syndroid.seed_guard")._guard(spy)(0, seed=np.uint64(3))
    assert type(seen[0]) is int and type(seen[0] + 1) is int


@pytest.mark.parametrize("name", MODS)
def test_public_names_wrap_the_core_function(name):
    m = mod(name)
    core = importlib.import_module(m.__name__.rsplit(".", 1)[0] + ".core")
    for fn in WRAPPERS[name]:
        assert getattr(m, fn).__wrapped__ is getattr(core, fn)


def test_check_seed_allow_none_and_plain_int():
    assert check_seed(5, allow_none=True) == 5 and type(check_seed(5, allow_none=True)) is int
    assert check_seed(np.int64(5), allow_none=True) == 5 and type(check_seed(np.int64(5), allow_none=True)) is int
    assert check_seed(None, allow_none=True) is None
    assert type(check_seed(np.int64(5))) is int
    with pytest.raises(TypeError, match=r"^seed must be an integer$"):
        check_seed(None)
    with pytest.raises(TypeError, match=r"^seed must be an integer$"):
        check_seed(True, allow_none=True)
    with pytest.raises(ValueError, match=r"^seed must be between 0 and 9223372036854775807$"):
        check_seed(-1, allow_none=True)
