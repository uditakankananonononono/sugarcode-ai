"""Forwarding and refusal pins for every seed_gate.py callable (13 modules, 27 functions plus the MLP class).

Core is replaced by a spy with core's exact signature. Each non-seed parameter gets its own sentinel object; the gate must hand
core the same object (identity) in the same parameter, whether the caller used keywords or positions. The seed is the only value
that changes: a valid seed arrives as a plain int equal to the one passed (numpy integers included); an invalid seed is refused with
the exact helper message and core is never called. Independent of the wrappers' own tests: expectations come from core's signature,
not from the gate's source.
"""
import importlib
import inspect

import numpy as np
import pytest

FILE = {"profile_hmm": "training", "qsar_bench": "model"}
GATE = {
    "molecule_eval": ["_ci", "evaluate_library", "compare_libraries"],
    "neohunter": ["simulate_immune_escape"],
    "neuro_pipeline": ["train", "lesion_study", "rsa", "predictive_coding_hierarchy", "pipeline_report", "neuro_diagnostics", "MLP"],
    "profile_hmm": ["random_profile_hmm"],
    "qsar_bench": ["_split_indices", "validate_qsar"],
    "stability_ai": ["stochastic_drift", "stochastic_drift_v2"],
    "str_scope": ["repeat_instability"],
    "syn_bio_studio": ["gillespie_expression"],
    "syn_stab_ai": ["population_simulation"],
    "synbio_wizard": ["gillespie_expression", "uncertainty_distribution"],
    "synlife_evo": ["evolve", "simulate_evolution_experiment", "simulate_competition"],
    "synthetic_life": ["stochastic_control", "ale_trajectory"],
    "virtual_cell": ["simulate_expression", "simulate_cell"],
}
ALL = [(m, f) for m, fs in GATE.items() for f in fs]
CAP = 2**63 - 1
GOOD_SEED = 12345


def setup(m, f, monkeypatch):
    gate = importlib.import_module(f"sugarcode.modules.{m}.seed_gate")
    core = importlib.import_module(f"sugarcode.modules.{m}.{FILE.get(m, 'core')}")
    seen = []
    if f == "MLP":
        target = core.MLP.__init__
        sig = inspect.signature(target)

        def spy(self, *a, **k):
            seen.append(dict(sig.bind(self, *a, **k).arguments))
        monkeypatch.setattr(core.MLP, "__init__", spy)
        params = [p for p in sig.parameters.values() if p.name != "self"]
        return gate.MLP, params, seen, True
    target = getattr(core, f)
    sig = inspect.signature(target)

    def spy(*a, **k):
        seen.append(dict(sig.bind(*a, **k).arguments))
        return "SENTINEL"
    monkeypatch.setattr(gate.core, f, spy)
    return getattr(gate, f), list(sig.parameters.values()), seen, False


def sentinels(params, seed):
    return {p.name: (seed if p.name == "seed" else object()) for p in params}


def check_forwarded(seen, params, sent, seed_expected):
    assert len(seen) == 1
    got = seen[0]
    for p in params:
        if p.name == "seed":
            assert got["seed"] == seed_expected and type(got["seed"]) is int
        else:
            assert got[p.name] is sent[p.name], p.name


@pytest.mark.parametrize("m,f", ALL)
def test_keyword_call_forwards_every_parameter_by_identity(m, f, monkeypatch):
    fn, params, seen, is_cls = setup(m, f, monkeypatch)
    sent = sentinels(params, GOOD_SEED)
    result = fn(**sent)
    if not is_cls:
        assert result == "SENTINEL"
    check_forwarded(seen, params, sent, GOOD_SEED)


@pytest.mark.parametrize("m,f", ALL)
def test_positional_call_forwards_every_parameter_by_identity(m, f, monkeypatch):
    fn, params, seen, _ = setup(m, f, monkeypatch)
    sent = sentinels(params, GOOD_SEED)
    pos = [sent[p.name] for p in params if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
    kw = {p.name: sent[p.name] for p in params if p.kind is p.KEYWORD_ONLY}
    fn(*pos, **kw)
    check_forwarded(seen, params, sent, GOOD_SEED)


@pytest.mark.parametrize("seed", [0, CAP, np.int64(7), np.uint64(CAP), np.int32(0)])
@pytest.mark.parametrize("m,f", ALL)
def test_valid_seed_forwarded_as_plain_int(m, f, seed, monkeypatch):
    fn, params, seen, _ = setup(m, f, monkeypatch)
    sent = sentinels(params, seed)
    fn(**sent)
    check_forwarded(seen, params, sent, int(seed))


@pytest.mark.parametrize("bad,exc,text", [
    (True, TypeError, "seed must be an integer"), (False, TypeError, "seed must be an integer"),
    (1.0, TypeError, "seed must be an integer"), ("1", TypeError, "seed must be an integer"),
    (None, TypeError, "seed must be an integer"), ([1], TypeError, "seed must be an integer"),
    (np.bool_(True), TypeError, "seed must be an integer"),
    (-1, ValueError, f"seed must be between 0 and {CAP}"), (CAP + 1, ValueError, f"seed must be between 0 and {CAP}"),
])
@pytest.mark.parametrize("m,f", ALL)
def test_invalid_seed_is_refused_before_core(m, f, bad, exc, text, monkeypatch):
    fn, params, seen, _ = setup(m, f, monkeypatch)
    sent = sentinels(params, bad)
    with pytest.raises(exc) as e:
        fn(**sent)
    assert str(e.value) == text
    assert seen == []


@pytest.mark.parametrize("m,f", ALL)
def test_omitted_parameters_reach_core_with_core_defaults(m, f, monkeypatch):
    """Call with only the required parameters: every omitted parameter, seed included, must reach core equal to core's own default."""
    fn, params, seen, _ = setup(m, f, monkeypatch)
    required = {p.name: (GOOD_SEED if p.name == "seed" else object()) for p in params if p.default is inspect.Parameter.empty}
    pos = [required[p.name] for p in params if p.name in required and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
    kw = {p.name: required[p.name] for p in params if p.name in required and p.kind is p.KEYWORD_ONLY}
    fn(*pos, **kw)
    assert len(seen) == 1
    got = seen[0]
    defaults = [p for p in params if p.default is not inspect.Parameter.empty]
    assert defaults, (m, f)  # every callable has at least one default (the seed), so this test is never vacuous
    for p in defaults:
        assert got[p.name] == p.default and type(got[p.name]) is type(p.default), (m, f, p.name)
        if p.default is None:
            assert got[p.name] is None
    for name, obj in required.items():
        assert got[name] == obj if name == "seed" else got[name] is obj


@pytest.mark.parametrize("m,f", ALL)
def test_gate_signature_defaults_equal_core(m, f, monkeypatch):
    gate = importlib.import_module(f"sugarcode.modules.{m}.seed_gate")
    core = importlib.import_module(f"sugarcode.modules.{m}.{FILE.get(m, 'core')}")
    g = gate.MLP.__init__ if f == "MLP" else getattr(gate, f)
    c = core.MLP.__init__ if f == "MLP" else getattr(core, f)
    gs = [(p.name, p.kind, p.default) for p in inspect.signature(g).parameters.values()]
    cs = [(p.name, p.kind, p.default) for p in inspect.signature(c).parameters.values()]
    assert gs == cs
