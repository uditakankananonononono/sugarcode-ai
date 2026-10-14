"""Strict public-design seed gates, separately from legacy characterization."""
import importlib
import re

import numpy as np
import pytest

CASES = [
    ('promoter_lib', 'design_promoter', (), {}),
    ('promoter_lib', 'generate_library', (), {'n': 2}),
    ('chemgpt_engine', 'generate', (), {'n': 2}),
    ('chemgpt_engine', 'generate_conditioned', (), {'n': 2}),
    ('vector_opt', 'engineer_capsid', (), {'n_variants': 2}),
    ('protein_painter', 'design_protein', ('enzyme',), {'candidates': 1}),
    ('riboswitch', 'design_riboswitch', ('theophylline',), {}),
    ('cellfatenet', 'design_fate_transition', ({}, {}), {}),
    ('codon_opt', 'design_expression_construct', ('M',), {}),
    ('crispr_muse', 'MuseAgent', (), {}),
]
CAP = 2**63 - 1

@pytest.mark.parametrize('module,name,args,kwargs', CASES)
@pytest.mark.parametrize('raw,error,message', [
    (None, TypeError, 'seed must be an integer'),
    (True, TypeError, 'seed must be an integer'),
    (np.bool_(True), TypeError, 'seed must be an integer'),
    (1.0, TypeError, 'seed must be an integer'),
    ('7', TypeError, 'seed must be an integer'),
    ([[]], TypeError, 'seed must be an integer'),
    (-1, ValueError, 'seed must be between 0 and 9223372036854775807'),
    (CAP + 1, ValueError, 'seed must be between 0 and 9223372036854775807')])
def test_invalid_seed_refused_before_any_work(monkeypatch, module, name, args, kwargs, raw, error, message):
    core = importlib.import_module('sugarcode.modules.' + module + '.core')
    package = importlib.import_module('sugarcode.modules.' + module)
    calls = []
    def unexpected(*a, **k):
        calls.append((a, k))
        raise AssertionError('core work started before seed refusal')
    if module == 'cellfatenet': monkeypatch.setattr(core, 'identify_attractors', unexpected)
    elif module == 'codon_opt': monkeypatch.setattr(core, '_validate_design', unexpected)
    elif module == 'crispr_muse': monkeypatch.setattr(core.np.random, 'default_rng', unexpected)
    else: monkeypatch.setattr(core.random, 'Random', unexpected)
    with pytest.raises(error, match='^' + re.escape(message) + '$'):
        getattr(package, name)(*args, seed=raw, **kwargs)
    assert calls == []

@pytest.mark.parametrize('module,name,args,kwargs', CASES)
@pytest.mark.parametrize('raw', [0, 7, CAP, np.int64(7), np.uint64(CAP)])
def test_valid_seed_is_plain_int_before_any_work(monkeypatch, module, name, args, kwargs, raw):
    core = importlib.import_module('sugarcode.modules.' + module + '.core')
    package = importlib.import_module('sugarcode.modules.' + module)
    seen = []
    class Stop(Exception): pass
    def stop(seed):
        seen.append(seed)
        raise Stop
    if module == 'cellfatenet':
        monkeypatch.setattr(core, 'identify_attractors', lambda **k: stop(k['seed']))
    elif module == 'codon_opt':
        monkeypatch.setattr(core, '_validate_design', lambda *a: 'M')
        monkeypatch.setattr(core, 'optimize', lambda *a: {'optimized_dna': 'ATG'})
        for helper in ('tasep_simulate', 'metabolic_load', 'folding_accessibility'):
            monkeypatch.setattr(core, helper, lambda *a, **k: {})
        monkeypatch.setattr(core, 'evolutionary_robustness', lambda *a, **k: stop(k['seed']))
    elif module == 'crispr_muse': monkeypatch.setattr(core.np.random, 'default_rng', stop)
    else: monkeypatch.setattr(core.random, 'Random', stop)
    with pytest.raises(Stop): getattr(package, name)(*args, seed=raw, **kwargs)
    assert len(seen) == 1 and type(seen[0]) is int and seen[0] == int(raw)

@pytest.mark.parametrize('module,name,args,kwargs', CASES[:7])
def test_numpy_seed_matches_python_seed_in_actual_design(module, name, args, kwargs):
    fn = getattr(importlib.import_module('sugarcode.modules.' + module), name)
    assert fn(*args, seed=np.int64(7), **kwargs) == fn(*args, seed=7, **kwargs)

def test_riboswitch_seed_still_has_no_output_effect():
    from sugarcode.modules.riboswitch import design_riboswitch
    assert design_riboswitch('theophylline', seed=0) == design_riboswitch('theophylline', seed=CAP)

def test_muse_numpy_seed_is_normalized_without_changing_sampling():
    from sugarcode.modules.crispr_muse import MuseAgent
    a = MuseAgent(seed=np.int64(7))
    assert type(a.seed) is int
    assert a.sample_guides(2) == MuseAgent(seed=7).sample_guides(2)

@pytest.mark.parametrize('raw', [None, True, [[]], np.int64(7)])
def test_generate_conditioned_checks_before_its_generate_callee(monkeypatch, raw):
    from sugarcode.modules.chemgpt_engine import core
    seen = []
    class Stop(Exception): pass
    def spy(n, logp, seed):
        seen.append(seed)
        raise Stop
    monkeypatch.setattr(core, 'generate', spy)
    if isinstance(raw, np.integer):
        with pytest.raises(Stop):core.generate_conditioned(seed=raw)
        assert type(seen[0]) is int and seen[0] == 7
    else:
        with pytest.raises(TypeError, match='^seed must be an integer$'):core.generate_conditioned(seed=raw)
        assert seen == []
