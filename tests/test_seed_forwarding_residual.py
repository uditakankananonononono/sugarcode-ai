"""Sweep wrappers: every public wrapper hands core a plain Python int and really wraps the core function."""
import importlib

import numpy as np
import pytest

from sugarcode.seed_check import MAX_SEED

WRAPPERS = {
    'modules.neuro_pipeline.seed_checked_study': ['lesion_study', 'rsa'],
    'llm.seed_checked_router': ['train_softmax'],
}
CORES = {
    'modules.neuro_pipeline.seed_checked_study': 'sugarcode.modules.neuro_pipeline.core',
    'llm.seed_checked_router': 'sugarcode.llm.router',
}
MODS = sorted(WRAPPERS)


def mod(name):
    return importlib.import_module("sugarcode." + name)


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


@pytest.mark.parametrize("name", MODS)
def test_public_names_wrap_the_core_function(name):
    m = mod(name)
    core = importlib.import_module(CORES[name])
    for fn in WRAPPERS[name]:
        assert getattr(m, fn).__wrapped__ is getattr(core, fn)
