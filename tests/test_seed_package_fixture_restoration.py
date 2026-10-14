"""Regression pins for package-spy teardown after a cold wrapper import."""
import importlib
import sys

import pytest

from test_seed_package_export_contract import package_spy


@pytest.mark.parametrize('wrapper_present', [False, True])
def test_package_spy_restores_real_binding_after_cold_or_warm_import(wrapper_present):
    module_name = 'sugarcode.modules.bio_copilot.seed_checked'
    package = importlib.import_module('sugarcode.modules.bio_copilot')
    core = importlib.import_module('sugarcode.modules.bio_copilot.core')
    original_module = importlib.import_module(module_name)
    package_state = dict(vars(package))
    real = core.propagate_uncertainty
    patch = pytest.MonkeyPatch()
    fixture = None
    try:
        if not wrapper_present:
            sys.modules.pop(module_name)
            package.__dict__.pop('seed_checked', None)
        fixture = package_spy.__wrapped__(patch)
        make = next(fixture)
        fn, signature, calls = make(module_name, core.__name__, 'propagate_uncertainty')
        assert fn.__wrapped__ is not real
        with pytest.raises(StopIteration):
            next(fixture)
        fixture = None
        restored = importlib.import_module(module_name)
        assert core.propagate_uncertainty is real
        assert restored.propagate_uncertainty.__wrapped__ is real
        assert package.propagate_uncertainty is package_state["propagate_uncertainty"]
        assert package.propagate_uncertainty.__wrapped__ is real
        assert calls == []
    finally:
        if fixture is not None:
            fixture.close()
        patch.undo()
        sys.modules[module_name] = original_module
        package.__dict__.clear()
        package.__dict__.update(package_state)
