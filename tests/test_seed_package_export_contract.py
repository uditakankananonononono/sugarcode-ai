"""Package re-exports must keep checked-wrapper forwarding and refusal."""
import importlib
import inspect
import re

import numpy as np
import pytest

from test_seed_wrapper_export_contract import CASES, inputs

EXCLUDED = {('sugarcode.llm.seed_checked_router', 'train_softmax'),
            ('sugarcode.modules.docking_studio.seed_checked_vina', 'dock'),
            ('sugarcode.modules.docking_studio.seed_checked_vina', 'prepare_ligand_from_smiles')}
PACKAGE_CASES = [(m, c, n) for m, c, n in CASES if (m, n) not in EXCLUDED]
CAP = 2**63 - 1

@pytest.fixture
def package_spy(monkeypatch):
    touched = []
    def make(module, coremodule, name):
        core = importlib.import_module(coremodule)
        sig = inspect.signature(getattr(core, name))
        calls = []
        def spy(*args, **kwargs):
            bound = sig.bind(*args, **kwargs)
            calls.append(dict(bound.arguments))
            bound.apply_defaults()
            return dict(bound.arguments)
        spy.__signature__ = sig
        wrapper = importlib.import_module(module)
        package = importlib.import_module(module.rsplit('.', 1)[0])
        touched.append((wrapper, dict(vars(wrapper)), package, dict(vars(package))))
        monkeypatch.setattr(core, name, spy)
        importlib.reload(wrapper)
        importlib.reload(package)
        assert getattr(package, name) is getattr(wrapper, name)
        return getattr(package, name), sig, calls
    yield make
    monkeypatch.undo()
    for wrapper, wrapper_state, package, package_state in reversed(touched):
        wrapper.__dict__.clear()
        wrapper.__dict__.update(wrapper_state)
        package.__dict__.clear()
        package.__dict__.update(package_state)

@pytest.mark.parametrize('module,coremodule,name', PACKAGE_CASES)
@pytest.mark.parametrize('style', ['positional', 'keyword', 'mixed'])
@pytest.mark.parametrize('seed', [0, CAP, np.int64(7)])
def test_package_preserves_all_forwarded_slots(package_spy, module, coremodule, name, style, seed):
    fn, sig, calls = package_spy(module, coremodule, name)
    args, kwargs, expected = inputs(sig, seed, style)
    result = fn(*args, **kwargs)
    assert len(calls) == 1
    assert inspect.signature(fn) == sig
    for key, value in expected.items():
        if key == 'seed':
            assert type(result[key]) is int and result[key] == int(seed)
        else:
            assert result[key] is value

@pytest.mark.parametrize('module,coremodule,name', PACKAGE_CASES)
@pytest.mark.parametrize('seed,error,message', [
    (None, TypeError, 'seed must be an integer'),
    (True, TypeError, 'seed must be an integer'),
    ([[]], TypeError, 'seed must be an integer'),
    (-1, ValueError, 'seed must be between 0 and 9223372036854775807')])
def test_package_refuses_before_core(package_spy, module, coremodule, name, seed, error, message):
    fn, sig, calls = package_spy(module, coremodule, name)
    args, kwargs, _ = inputs(sig, seed, 'mixed')
    with pytest.raises(error, match='^' + re.escape(message) + '$'):
        fn(*args, **kwargs)
    assert calls == []

@pytest.mark.parametrize('module,coremodule,name', PACKAGE_CASES)
def test_package_omission_uses_core_defaults(package_spy, module, coremodule, name):
    fn, sig, calls = package_spy(module, coremodule, name)
    required = {n: object() for n, p in sig.parameters.items() if p.default is inspect.Parameter.empty}
    result = fn(**required)
    assert calls == [required]
    for n, p in sig.parameters.items():
        assert result[n] is (required[n] if n in required else p.default)
