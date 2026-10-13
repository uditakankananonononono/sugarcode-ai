"""Seed-checked entry points for docking_studio.vina_real functions that pass `seed` to RDKit EmbedMolecule / AutoDock Vina.

Only the seed is checked (shared helper: int or numpy integer, not bool, 0..2**63-1); every other argument goes to vina_real unchanged.
"""
from __future__ import annotations

import functools
import inspect

from sugarcode.seed_check import check_seed

from . import vina_real


def _guard(fn):
    sig = inspect.signature(fn)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        if "seed" in bound.arguments:
            bound.arguments["seed"] = check_seed(bound.arguments["seed"])
        return fn(*bound.args, **bound.kwargs)

    return wrapper


prepare_ligand_from_smiles = _guard(vina_real.prepare_ligand_from_smiles)
dock = _guard(vina_real.dock)
