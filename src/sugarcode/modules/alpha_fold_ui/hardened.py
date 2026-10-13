"""Hardened validating wrappers for alpha_fold_ui (additive; core.py untouched).

Defects on b363c3b: mutation_stability(position=-1) silently scores the LAST residue (negative index
wrap) and float positions are truncated (1.7 -> 1); physical_energy accepts nan coordinates and returns a
finite energy (nan pair distance dropped by max(.5, nan)), sigma=0 gives energy 0; rigid_transform accepts a
non-orthogonal rotation (a 2x scaling matrix doubles all distances) although it is documented as rigid;
refine_coordinates(learning_rate=nan) returns nan coordinates, learning_rate=1e9 returns coordinates ~1e10,
steps=-5 silently returns the input, steps=10**9 does not return; residue_graph accepts nan/negative cutoff.
Composition/LJ heuristics on a CA trace only; no structure-prediction accuracy claim.
"""
from __future__ import annotations
import math
import numpy as np
from . import core

MAX_RESIDUES = 400
MAX_STEPS = 500


def _num(name, v, lo, hi):
    if isinstance(v, bool):
        raise ValueError(f"{name}: bool is not a number")
    if not isinstance(v, (int, float)):
        raise ValueError(f"{name}: must be int or float")
    if abs(v) > 10**9:
        raise ValueError(f"{name}: magnitude exceeds cap")
    v = float(v)
    if not math.isfinite(v):
        raise ValueError(f"{name}: must be finite")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: out of range [{lo}, {hi}]")
    return v


def _int(name, v, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError(f"{name}: must be int")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: must be in [{lo}, {hi}]")
    return v


def _coords(c, min_n=1):
    try:
        a = np.asarray(c, dtype=float)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("coords: numeric (n, 3) array required")
    if a.ndim != 2 or a.shape[1] != 3 or not min_n <= a.shape[0] <= MAX_RESIDUES:
        raise ValueError(f"coords: shape (n, 3) with {min_n} <= n <= {MAX_RESIDUES} required")
    if not np.all(np.isfinite(a)) or np.max(np.abs(a)) > 1e6:
        raise ValueError("coords: finite values with |x| <= 1e6 required")
    return a


def _tree_ok(x):
    if isinstance(x, dict):
        return all(_tree_ok(v) for v in x.values())
    if isinstance(x, (list, tuple)):
        return all(_tree_ok(v) for v in x)
    if isinstance(x, np.ndarray):
        return bool(np.all(np.isfinite(x)))
    if isinstance(x, (float, np.floating)):
        return math.isfinite(float(x))
    return True


def safe_mutation_stability(sequence, position, mutant):
    if not isinstance(sequence, str) or not sequence or len(sequence) > 100_000:
        raise ValueError("sequence: non-empty str required")
    seq = ''.join(a for a in sequence.upper() if a in core.CF)
    p = _int("position", position, 0, len(seq) - 1 if seq else -1)
    if not isinstance(mutant, str) or len(mutant) != 1 or mutant not in core.CF:
        raise ValueError("mutant: one of the 20 uppercase amino-acid letters required")
    return core.mutation_stability(sequence, p, mutant)


def safe_rigid_transform(coords, rotation, translation):
    c = _coords(coords)
    try:
        r = np.asarray(rotation, dtype=float)
        t = np.asarray(translation, dtype=float)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("rotation/translation: numeric arrays required")
    if r.shape != (3, 3) or t.shape != (3,) or not np.all(np.isfinite(r)) or not np.all(np.isfinite(t)):
        raise ValueError("rotation must be finite 3x3 and translation finite length-3")
    if np.max(np.abs(t)) > 1e6:
        raise ValueError("translation: |x| <= 1e6 required")
    if not np.allclose(r @ r.T, np.eye(3), rtol=0, atol=1e-8) or not np.isclose(np.linalg.det(r), 1.0, rtol=0, atol=1e-8):
        raise ValueError("rotation must be a proper rotation (orthonormal, det +1)")
    return core.rigid_transform(c, r, t)


def _charges(charges, n):
    if charges is None:
        return None
    try:
        q = np.asarray(charges, dtype=float)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("charges: numeric vector required")
    if q.shape != (n,) or not np.all(np.isfinite(q)) or np.max(np.abs(q)) > 1e3:
        raise ValueError("charges: finite vector with one entry per residue, |q| <= 1e3, required")
    return q


def safe_physical_energy(coords, charges=None, sigma=3.8, epsilon=.1):
    c = _coords(coords)
    s = _num("sigma", sigma, 1e-3, 100.0)
    e = _num("epsilon", epsilon, 0.0, 1e6)
    q = _charges(charges, len(c))
    out = core.physical_energy(c, q, s, e)
    if not _tree_ok(out):
        raise ValueError("non-finite output refused")
    return out


def safe_residue_graph(coords, cutoff=8):
    c = _coords(coords)
    k = _num("cutoff", cutoff, 0.0, 1e4)
    return core.residue_graph(c, k)


def safe_refine_coordinates(coords, charges=None, steps=20, learning_rate=.002, restrain_bonds=True,
                            bond_length=3.8, k_bond=10.0):
    c = _coords(coords, 2)
    if len(c) > 60:
        raise ValueError("coords: refinement limited to 60 residues (finite-difference gradient is O(n^3))")
    q = _charges(charges, len(c))
    n_steps = _int("steps", steps, 1, MAX_STEPS)
    lr = _num("learning_rate", learning_rate, 0.0, 0.1)
    if not isinstance(restrain_bonds, bool):
        raise ValueError("restrain_bonds: bool required")
    bl = _num("bond_length", bond_length, 0.5, 20.0)
    kb = _num("k_bond", k_bond, 0.0, 1e4)
    out = core.refine_coordinates(c, q, n_steps, lr, restrain_bonds, bl, kb)
    if not _tree_ok(out) or np.max(np.abs(np.asarray(out["coordinates"]))) > 1e6:
        raise ValueError("non-finite or exploded output refused")
    return out
