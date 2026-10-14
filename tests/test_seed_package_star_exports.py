"""Checked seed package exports include declared names and the real Vina aliases."""
import importlib

import numpy as np
import pytest

from test_seed_wrapper_export_contract import CASES, inputs
from test_seed_package_export_contract import package_spy

EXPORT_CASES = [(m, c, n, n) for m, c, n in CASES
                if not m.endswith(('seed_checked_router', 'seed_checked_vina'))]
EXPORT_CASES += [
    ('sugarcode.modules.docking_studio.seed_checked_vina', 'sugarcode.modules.docking_studio.vina_real', 'dock', 'dock_vina_real'),
    ('sugarcode.modules.docking_studio.seed_checked_vina', 'sugarcode.modules.docking_studio.vina_real', 'prepare_ligand_from_smiles', 'prepare_ligand_vina_real'),
]

@pytest.mark.parametrize('module,coremodule,name,export', EXPORT_CASES)
def test_all_and_star_import_preserve_checked_function(module, coremodule, name, export):
    package_name = module.rsplit('.', 1)[0]
    package = importlib.import_module(package_name)
    wrapper = importlib.import_module(module)
    assert export in package.__all__
    namespace = {}
    exec('from ' + package_name + ' import *', namespace)
    assert namespace[export] is getattr(wrapper, name)
    assert getattr(package, export) is getattr(wrapper, name)

@pytest.mark.parametrize('name,export', [('dock', 'dock_vina_real'), ('prepare_ligand_from_smiles', 'prepare_ligand_vina_real')])
@pytest.mark.parametrize('style', ['positional', 'keyword', 'mixed'])
def test_vina_alias_forwards_and_refuses(monkeypatch, name, export, style):
    module = importlib.import_module('sugarcode.modules.docking_studio.seed_checked_vina')
    core = importlib.import_module('sugarcode.modules.docking_studio.vina_real')
    package = importlib.import_module('sugarcode.modules.docking_studio')
    import inspect
    sig = inspect.signature(getattr(core, name))
    calls = []
    def spy(*a, **k):
        b = sig.bind(*a, **k)
        calls.append(dict(b.arguments))
        return dict(b.arguments)
    spy.__signature__ = sig
    wrapper_state = dict(vars(module))
    package_state = dict(vars(package))
    try:
        monkeypatch.setattr(core, name, spy)
        importlib.reload(module)
        importlib.reload(package)
        fn = getattr(package, export)
        args, kwargs, expected = inputs(sig, np.int64(7), style)
        result = fn(*args, **kwargs)
        for key, value in expected.items():
            if key == 'seed': assert type(result[key]) is int and result[key] == 7
            else: assert result[key] is value
        calls.clear()
        args, kwargs, _ = inputs(sig, [[]], style)
        with pytest.raises(TypeError, match='^seed must be an integer$'): fn(*args, **kwargs)
        assert calls == []
    finally:
        monkeypatch.undo()
        module.__dict__.clear()
        module.__dict__.update(wrapper_state)
        package.__dict__.clear()
        package.__dict__.update(package_state)

def test_llm_router_is_explicit_adapter_not_package_export():
    package = importlib.import_module('sugarcode.llm')
    assert 'train_softmax' not in package.__all__
    assert not hasattr(package, 'train_softmax')
