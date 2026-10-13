"""Defaults and signatures of every seed_gate.py wrapper (13 modules, 28 callables: 27 functions plus the MLP class).

1. Signature equality with core: parameter names, kinds and defaults (an edited default in the gate would otherwise only change
   behavior when the caller omits that argument).
2. Default-seed / default-argument call equals core's own call with the same explicit arguments (calls use only the arguments
   that are required or shrink the run; every parameter that has a default is left at its default).
"""
import importlib
import inspect
import re

import numpy as np
import pytest

FILE = {"profile_hmm": "training", "qsar_bench": "model"}
GATE = {
    "molecule_eval": ["_ci", "evaluate_library", "compare_libraries"],
    "neohunter": ["simulate_immune_escape"],
    "neuro_pipeline": ["train", "lesion_study", "rsa", "predictive_coding_hierarchy", "pipeline_report", "neuro_diagnostics"],
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
SIG = [(m, f) for m, fs in GATE.items() for f in fs]
CASES = [
    ('molecule_eval', 'evaluate_library', "['CCO','CCN','CCC','CCCl']"),
    ('molecule_eval', 'compare_libraries', "['CCO','CCN','CCC'], ['CCO','CCCl','CCBr']"),
    ('neohunter', 'simulate_immune_escape', "[{'peptide':'SIINFEKL'}], generations=3, population=50"),
    ('neuro_pipeline', 'train', 'epochs=3'),
    ('neuro_pipeline', 'lesion_study', "__import__('sugarcode.modules.neuro_pipeline.core', fromlist=['x']).train(epochs=3, seed=1)['model']"),
    ('neuro_pipeline', 'rsa', "__import__('sugarcode.modules.neuro_pipeline.core', fromlist=['x']).train(epochs=3, seed=1)['model'], n_stimuli=5"),
    ('neuro_pipeline', 'predictive_coding_hierarchy', "__import__('numpy').ones((6,4)), steps=2, epochs=2"),
    ('neuro_pipeline', 'pipeline_report', ''),
    ('neuro_pipeline', 'neuro_diagnostics', ''),
    ('profile_hmm', 'random_profile_hmm', '4'),
    ('qsar_bench', 'validate_qsar', "['CCO','CCN','CCC','CCCl','CCBr','CCI','CCF','CCS','CCP','CC'], [1,2,3,4,5,6,7,8,9,10], strategy='random'"),
    ('str_scope', 'repeat_instability', '20, divisions=3, trajectories=5'),
    ('syn_bio_studio', 'gillespie_expression', 'duration=5'),
    ('syn_stab_ai', 'population_simulation', 'generations=5'),
    ('synbio_wizard', 'gillespie_expression', 'hours=2'),
    ('synbio_wizard', 'uncertainty_distribution', '1.0, samples=20'),
    ('synlife_evo', 'evolve', "['g1','g2'], generations=5, pop_size=20"),
    ('synlife_evo', 'simulate_evolution_experiment', "['g1','g2'], generations=12, population=200, sample_every=2"),
    ('synlife_evo', 'simulate_competition', "['g1','g2'], generations=12, population=200, sample_every=2"),
    ('synthetic_life', 'stochastic_control', 'hours=1'),
    ('synthetic_life', 'ale_trajectory', 'generations=5'),
    ('virtual_cell', 'simulate_expression', "['a','b'], [('a','b',1.0)], hours=2, points=5, method='gillespie'"),
    ('virtual_cell', 'simulate_cell', "hours=2, method='gillespie'"),
    ('stability_ai', 'stochastic_drift', "{'mode':'plasmid','burden':0.1,'size_kb':5}, generations=5, population=50, replicates=4"),
    ('stability_ai', 'stochastic_drift_v2', "{'mode':'plasmid','burden':0.1,'size_kb':5}, generations=5, population=50, replicates=4"),
]


def mods(m):
    gate = importlib.import_module(f"sugarcode.modules.{m}.seed_gate")
    core = importlib.import_module(f"sugarcode.modules.{m}.{FILE.get(m, 'core')}")
    return gate, core


def sig(fn):
    return [(p.name, p.kind, p.default) for p in inspect.signature(fn).parameters.values()]


def norm(x):
    return re.sub(r"0x[0-9a-f]+", "0x", repr(x))


def call(fn, argstr):
    ns = {"np": np, "__builtins__": __builtins__}
    return eval("(lambda f: f(" + argstr + "))", ns)(fn)


def outcome(fn, argstr):
    try:
        return ("ok", norm(call(fn, argstr)))
    except Exception as e:  # core's own refusals must also match
        return ("err", type(e).__name__, str(e))


def test_table_covers_every_gate_callable():
    for m, fs in GATE.items():
        gate, _ = mods(m)
        defined = {n for n, v in vars(gate).items() if not n.startswith("__") and callable(v) and getattr(v, "__module__", None) == gate.__name__}
        want = set(fs) | ({"MLP"} if m == "neuro_pipeline" else set())
        assert defined == want, (m, defined ^ want)
    assert len(GATE) == 13 and len(SIG) == 27 and len(CASES) == 25


@pytest.mark.parametrize("m,f", SIG)
def test_signature_equals_core(m, f):
    gate, core = mods(m)
    assert sig(getattr(gate, f)) == sig(getattr(core, f))
    assert len(sig(getattr(gate, f))) >= 1


def test_mlp_init_signature_equals_core():
    gate, core = mods("neuro_pipeline")
    assert sig(gate.MLP.__init__) == sig(core.MLP.__init__)
    assert issubclass(gate.MLP, core.MLP)


def test_mlp_default_seed_equals_core():
    gate, core = mods("neuro_pipeline")
    a, b = gate.MLP(6, 4, 2), core.MLP(6, 4, 2)
    for name, v in vars(b).items():
        w = getattr(a, name)
        if isinstance(v, np.ndarray):
            assert np.array_equal(w, v), name
        elif isinstance(v, (list, tuple)) and v and isinstance(v[0], np.ndarray):
            assert all(np.array_equal(x, y) for x, y in zip(w, v)), name
    assert vars(b), "MLP has no instance state to compare"


@pytest.mark.parametrize("m,f,argstr", CASES)
def test_default_call_equals_core(m, f, argstr):
    gate, core = mods(m)
    a = outcome(getattr(gate, f), argstr)
    b = outcome(getattr(core, f), argstr)
    assert a[0] == "ok", a  # compared path is a real result, not a shared error
    assert a == b


def test_helpers_equal_core_with_explicit_seed():
    g, c = mods("molecule_eval")
    vals = [0.1, 0.5, 0.9, 0.3, 0.7]
    assert norm(g._ci(vals, np.mean, 5)) == norm(c._ci(vals, np.mean, 5))
    assert norm(g._ci(vals, np.mean, 5, 50)) == norm(c._ci(vals, np.mean, 5, 50))
    g, c = mods("qsar_bench")
    smi = ["CCO", "CCN", "CCC", "CCCl", "CCBr", "CCI", "CCF", "CCS", "CCP", "CC"]
    assert norm(g._split_indices(smi, "random", 0.2, 5)) == norm(c._split_indices(smi, "random", 0.2, 5))
