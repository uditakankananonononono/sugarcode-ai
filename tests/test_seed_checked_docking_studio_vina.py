"""vina_real seed gate. RDKit and the vina package are not installed here, so the core failure on a nested-list seed
is NOT reproduced; these tests pin the gate with spies (forwarding, plain int, refusals before any heavy import)."""
import importlib
import inspect
import re

import numpy as np
import pytest

vr = importlib.import_module("sugarcode.modules.docking_studio.vina_real")
sc = importlib.import_module("sugarcode.modules.docking_studio.seed_checked_vina")
CAP = 2**63 - 1
NAMES = ["prepare_ligand_from_smiles", "dock"]


def msg(s):
    return re.escape(s) + "$"


def _args(fn):
    return ("CCO", "/tmp/x.pdbqt") if fn == "prepare_ligand_from_smiles" else ("r.pdbqt", "l.pdbqt", (0.0, 0.0, 0.0))


@pytest.mark.parametrize("fn", NAMES)
def test_wraps_core_and_signature(fn):
    assert getattr(sc, fn).__wrapped__ is getattr(vr, fn)
    assert inspect.signature(getattr(sc, fn)) == inspect.signature(getattr(vr, fn))


@pytest.mark.parametrize("fn", NAMES)
def test_refuses_bad_seeds_before_any_work(fn):
    w = getattr(sc, fn)
    for bad in (True, False, np.bool_(1), 1.0, "7", None, [1], b"7"):
        with pytest.raises(TypeError, match=msg("seed must be an integer")):
            w(*_args(fn), seed=bad)
    deep = []
    for _ in range(100000):
        deep = [deep]
    with pytest.raises(TypeError, match=msg("seed must be an integer")):
        w(*_args(fn), seed=deep)
    for bad in (-1, CAP + 1, 2**64, 10**400):
        with pytest.raises(ValueError, match=msg(f"seed must be between 0 and {CAP}")):
            w(*_args(fn), seed=bad)


@pytest.mark.parametrize("fn", NAMES)
def test_forwarding_plain_int_and_default_untouched(fn):
    seen = []
    sig = inspect.signature(getattr(vr, fn))

    def spy(*a, **k):
        seen.append(sig.bind(*a, **k).arguments.get("seed", "unset"))
        return "ok"

    spy.__signature__ = sig
    g = sc._guard(spy)
    for raw in (np.int64(5), np.uint8(7), 0, CAP, np.uint64(CAP)):
        assert g(*_args(fn), seed=raw) == "ok"
        assert type(seen[-1]) is int and seen[-1] == int(raw)
    g(*_args(fn))
    assert seen[-1] == "unset"
    n = len(seen)
    with pytest.raises(TypeError):
        g(*_args(fn), seed=None)
    assert len(seen) == n


def test_positional_seed_is_checked():
    with pytest.raises(TypeError, match=msg("seed must be an integer")):
        sc.prepare_ligand_from_smiles("CCO", "/tmp/x.pdbqt", [[]])
    with pytest.raises(ValueError, match=msg(f"seed must be between 0 and {CAP}")):
        sc.dock("r", "l", (0, 0, 0), (22.0, 22.0, 22.0), 8, 9, -1)
