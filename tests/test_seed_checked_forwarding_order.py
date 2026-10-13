"""Forwarding order for every seed-checked wrapper in the lane 5b set: each parameter gets a distinct sentinel object;
core must receive the same objects (identity) in the same parameter slots, whether the caller passed them
positionally or by keyword. The seed alone is replaced (by its checked plain int)."""
import importlib
import inspect

import numpy as np
import pytest

SETS = {
    "bio_copilot.seed_checked": ["propagate_uncertainty"],
    "bio_switch.seed_checked": ["gillespie_sensor_noise"],
    "bioplayground.seed_checked": ["run_sandbox", "directed_evolution"],
    "docking_studio.seed_checked": ["monte_carlo_dock"],
    "docking_studio.seed_checked_vina": ["prepare_ligand_from_smiles", "dock"],
    "phage_tx.seed_checked": ["evolve_cocktail"],
    "protein_painter.seed_checked": ["engineering_blueprint", "painter_diagnostics"],
    "riboswitch.seed_checked": ["optimize_switch"],
    "vector_opt.seed_checked": ["directed_evolution"],
}
CASES = [(m, f) for m, fns in SETS.items() for f in fns]


def _core_for(m):
    pkg = m.rsplit(".", 1)[0]
    return importlib.import_module("sugarcode.modules." + pkg + (".vina_real" if m.endswith("vina") else ".core"))


class S:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "S(%s)" % self.name


@pytest.mark.parametrize("m,fn", CASES)
@pytest.mark.parametrize("style", ["positional", "keyword", "mixed"])
@pytest.mark.parametrize("raw_seed", [5, np.int64(5)])
def test_distinct_sentinel_per_parameter_arrives_in_its_own_slot(m, fn, style, raw_seed):
    wrapper_mod = importlib.import_module("sugarcode.modules." + m)
    core_fn = getattr(_core_for(m), fn)
    sig = inspect.signature(core_fn)
    names = list(sig.parameters)
    assert "seed" in names
    sent = {n: S(n) for n in names if n != "seed"}
    sent["seed"] = raw_seed
    got = []

    def spy(*a, **k):
        got.append(sig.bind(*a, **k).arguments)
        return "ok"

    spy.__signature__ = sig
    g = wrapper_mod._guard(spy)
    kwonly = {n for n, p in sig.parameters.items() if p.kind is inspect.Parameter.KEYWORD_ONLY}
    if style == "positional":
        pos = [n for n in names if n not in kwonly]
        args = [sent[n] for n in pos]
        kw = {n: sent[n] for n in names if n in kwonly}
    elif style == "keyword":
        args, kw = [], {n: sent[n] for n in names}
    else:
        half = [n for n in names if n not in kwonly][: max(1, len(names) // 2)]
        args = [sent[n] for n in half]
        kw = {n: sent[n] for n in names if n not in half}
    assert g(*args, **kw) == "ok"
    seen = got[0]
    assert list(seen) == names          # every parameter delivered, in signature order
    for n in names:
        if n == "seed":
            assert type(seen[n]) is int and seen[n] == 5
        else:
            assert seen[n] is sent[n], n  # identity: no copy, no swap with another parameter
    # no extra defaults injected for omitted trailing parameters
    got.clear()
    required = [n for n, p in sig.parameters.items() if p.default is inspect.Parameter.empty and n != "seed"]
    g(**{n: sent[n] for n in required}, seed=raw_seed)
    assert set(got[0]) == set(required) | {"seed"}


@pytest.mark.parametrize("m,fn", CASES)
def test_wrapper_signature_equals_core_signature(m, fn):
    wrapper_mod = importlib.import_module("sugarcode.modules." + m)
    core_fn = getattr(_core_for(m), fn)
    w = getattr(wrapper_mod, fn)
    assert inspect.signature(w) == inspect.signature(core_fn)
    assert w.__wrapped__ is core_fn and w.__name__ == core_fn.__name__ and w.__doc__ == core_fn.__doc__
    assert list(inspect.signature(w).parameters) == list(inspect.signature(core_fn).parameters)
