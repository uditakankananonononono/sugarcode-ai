"""AUTHORED, NOT RUN. H12: evofold_4d.transition_trace diagonal double-count repair. Base 5c21515122c679408bd306886b2903ae428b4f2c.
Written BEFORE the source edit. Fixtures: tests/fixtures/h12_evofold/{oracle.json,coordinates.json}, byte-identical copies of the
peer-supplied frozen H12 oracle (ProDy 2.6.1, 1CRN chain A, 46 CA); sha256 pinned below and checked before use.
DELIBERATE INTERNALS TESTING: PRIMARY checks spy on numpy.linalg.eigh (a global numpy dependency: the spy patches the numpy.linalg
module attribute, so it sees every eigh call made while active). Call order inside transition_trace: call 1 = the Hessian solve inside
the unused anm_modes(...) call, call 2 (LAST) = transition_trace's own Hessian solve. Only the LAST call is used. No raw-frame
instrumentation and no reconstructed raw-frame claim: raw checks are limited to eigenvalues, the used mode vector and its projector.
SECONDARY checks compare ROUNDED public output (3 dp frames, 4 dp RMSD) to the oracle's ROUNDED frames. Internal-consistency checks
(rows sum to zero, six zero modes) are supplementary only, not the oracle."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from sugarcode.modules.evofold_4d.core import transition_trace

FIX = Path(__file__).resolve().parent / "fixtures" / "h12_evofold"
SHA = {"oracle.json": "098a99bb6d1c3922c003ed3f49d871d56ab94f59223ea3e66b3581fbd8b0bf98",
       "coordinates.json": "13f3e820715b178b0446bf5d6e3db963c47e4135b0be3fa633595deb70d079f3"}
STEPS, AMP = 20, 3.0


@pytest.fixture(scope="module")
def oracle():
    for name, want in SHA.items():
        assert hashlib.sha256((FIX / name).read_bytes()).hexdigest() == want
    return json.loads((FIX / "oracle.json").read_text())


@pytest.fixture(scope="module")
def coords():
    c = json.loads((FIX / "coordinates.json").read_text())
    assert len(c) == 46 and all(len(r) == 3 for r in c)
    return c


@pytest.fixture(scope="module")
def run(coords):
    """Run transition_trace once under a pass-through eigh spy; keep the LAST call's input and output."""
    real = np.linalg.eigh
    calls = []

    def spy(a, *args, **kw):
        out = real(a, *args, **kw)
        calls.append((np.array(a, copy=True), np.array(out[0], copy=True), np.array(out[1], copy=True)))
        return out

    np.linalg.eigh = spy
    try:
        result = transition_trace(coords, mode_index=0, steps=STEPS, amplitude=AMP)
    finally:
        np.linalg.eigh = real
    return result, calls


def _close(x, ref, abs_tol, rel_tol):
    return abs(x - ref) <= abs_tol or abs(x - ref) <= rel_tol * abs(ref)


def test_oracle_cluster_is_nondegenerate_so_sign_only_applies(oracle):
    assert oracle["first_cluster_dimension"] == 1 and oracle["first_mode_cluster_indices"] == [0]
    ph = AMP * np.sin(np.pi * np.arange(STEPS) / (STEPS - 1))
    assert np.allclose(ph, oracle["phases"], atol=1e-12, rtol=0)


def test_spy_saw_the_calls_and_last_call_is_the_3n_hessian(run):
    _, calls = run
    assert len(calls) >= 1  # call order: anm_modes' solve first, transition_trace's own solve LAST
    H, vals, vecs = calls[-1]
    assert H.shape == (138, 138) and vals.shape == (138,) and vecs.shape == (138, 138)


def test_primary_raw_eigenvalues_match_oracle(run, oracle):
    _, calls = run
    _, vals, _ = calls[-1]
    first12 = oracle["first12_eigenvalues"]
    tol = oracle["tolerances_frozen_before_repair"]
    # the code's own zero threshold is 1e-6; six rigid-body zeros must precede the first positive mode
    assert np.all(np.abs(vals[:6]) < 1e-6) and vals[6] > 1e-6
    for got, ref in zip(vals[6:18], first12):
        assert _close(float(got), ref, tol["eigenvalue_absolute"], tol["eigenvalue_relative"])


def test_primary_raw_mode_and_projector_1e7(run, oracle):
    _, calls = run
    _, vals, vecs = calls[-1]
    tol = oracle["tolerances_frozen_before_repair"]
    nz = [i for i, v in enumerate(vals) if v > 1e-6]
    v = vecs[:, nz[0]]
    u = np.array(oracle["first_mode_canonical_displacement_unit"]).reshape(-1)
    assert abs(np.linalg.norm(v) - 1.0) < 1e-9
    sign = 1.0 if float(v @ u) >= 0 else -1.0  # ONE global sign
    assert np.linalg.norm(sign * v - u) <= tol["raw_mode_vector_L2_after_sign_alignment"]
    P = np.array(oracle["first_cluster_projector"])
    assert np.max(np.abs(np.outer(v, v) - P)) <= tol["projector_max_absolute"]


def test_secondary_rounded_public_frames_one_global_sign(run, oracle, coords):
    result, _ = run
    tol = oracle["tolerances_frozen_before_repair"]
    C0 = np.array(coords)
    got = np.array(result["frames"])
    ref_pos = np.array(oracle["reference_rounded3_frames"])
    ref_neg = np.round(2.0 * C0 - np.array(oracle["reference_unrounded_frames"]), 3)  # the other global sign
    assert got.shape == ref_pos.shape == (STEPS, 46, 3)
    err = min(np.max(np.abs(got - ref_pos)), np.max(np.abs(got - ref_neg)))  # one sign for ALL frames
    assert err <= tol["reported_frame_coordinate_A_absolute"]


def test_secondary_rounded_rmsd_and_max(run, oracle):
    result, _ = run
    tol = oracle["tolerances_frozen_before_repair"]
    ref = oracle["reference_rounded4_RMSD_A"]
    assert len(result["rmsd_trace"]) == STEPS
    assert max(abs(a - b) for a, b in zip(result["rmsd_trace"], ref)) <= tol["reported_RMSD_A_absolute"]
    assert result["max_rmsd"] == max(result["rmsd_trace"])


def test_supplementary_hessian_rows_sum_to_zero(run):
    """Internal consistency only (supplementary): translation invariance; fails if diagonals are double counted."""
    _, calls = run
    H, _, _ = calls[-1]
    n = H.shape[0] // 3
    for i in range(n):
        row = sum(H[3 * i:3 * i + 3, 3 * j:3 * j + 3] for j in range(n))
        assert np.max(np.abs(row)) < 1e-9
    assert np.max(np.abs(H - H.T)) < 1e-12
