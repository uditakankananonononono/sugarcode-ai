"""AUTHORED, NOT RUN. H17: chemgpt_engine mass contract against the frozen Batch Av3 evidence (peer-supplied, RDKit 2025.9.1, run 2026-10-10,
archive SHA 7b60ab42b56b7d1fe453d6127ceaaa0c771c84991541a4bf7041d528fedd1ea0). Base ea586991bad79824470f156578095992d2f69610. Test and contract only: product code is untouched.
The frozen data is vendored byte-identical and hash-pinned; no RDKit, no network, nothing regenerated, no mass is invented for the refused inputs.
Assertions (final peer ruling):
 (i)   public mw == round(the module's own raw sum fragment masses - 2.016*(n-1), 1)   (self-consistency / rounding pin)
 (ii)  raw sum within 0.05 (ABS, unrounded, no epsilon) of the frozen RDKit reference_mass   (chemistry check)
 (iii) public mw == the frozen historical module_mass for each of the 148 returned cases   (regression)
 The earlier predicate round(frozen reference) == public mw is withdrawn (ill-posed: it compares a rounded RDKit tie to the module's rounded sum)."""
import hashlib
import json
from pathlib import Path

import pytest

from sugarcode.modules.chemgpt_engine.core import FRAGMENT_MW, score_molecule

FIX = Path(__file__).with_name("fixtures")
RESULTS = FIX / "h17_chemgpt_third_results.json"
FREEZE = FIX / "h17_chemgpt_third_input_freeze.json"
RESULTS_SHA256 = "635d7a5214bdb6d5a1c97bb1f95194f0d2a9f4822db6684a02a60e6e589a3dff"
FREEZE_SHA256 = "1225dda03a43152fed594321352969af4bfa852dd623f0fbbdd204cfbb67b984"
HISTORICAL_FAIL = {("carboxyl", "amide"): 89.0, ("ethyl_link", "sulfonamide"): 109.1, ("sulfonamide", "ethyl_link"): 109.1}


def _rows():
    return json.loads(RESULTS.read_text())["chemgpt_engine"]


def _returned():
    return [r for r in _rows() if not r.get("refused")]


def _raw(fs):
    return sum(FRAGMENT_MW[f] for f in fs) - 2.016 * (len(fs) - 1)


def test_vendored_frozen_files_are_hash_pinned():
    assert hashlib.sha256(RESULTS.read_bytes()).hexdigest() == RESULTS_SHA256
    assert hashlib.sha256(FREEZE.read_bytes()).hexdigest() == FREEZE_SHA256


def test_all_156_inputs_are_accounted_for_in_frozen_order():
    frozen = json.loads(FREEZE.read_text())["fragment_cases"]
    rows = _rows()
    assert [r["fragments"] for r in rows] == frozen
    assert len(frozen) == 156 and sum(len(x) == 1 for x in frozen) == 12 and sum(len(x) == 2 for x in frozen) == 144
    assert len(_returned()) == 148 and sum(bool(r.get("refused")) for r in rows) == 8


def test_eight_refusals_are_refusals_and_carry_no_mass():
    refused = [r for r in _rows() if r.get("refused")]
    assert len(refused) == 8 and all(r["fragments"][0] == "fluorine" and len(r["fragments"]) == 2 for r in refused)
    for r in refused:
        assert "module_mass" not in r and "reference_mass" not in r and "mass_abs_error" not in r
        with pytest.raises(ValueError, match="fluorine cannot be the core"):
            score_molecule(r["fragments"])


def test_i_public_mw_is_round_of_own_raw_sum_for_all_148():
    for r in _returned():
        fs = r["fragments"]
        assert score_molecule(fs)["mw"] == round(_raw(fs), 1), fs


def test_ii_raw_unrounded_sum_within_005_of_frozen_rdkit_reference_for_all_148():
    for r in _returned():
        fs = r["fragments"]
        assert abs(_raw(fs) - r["reference_mass"]) <= 0.05, fs


def test_iii_public_mw_equals_frozen_historical_module_mass_for_all_148():
    for r in _returned():
        assert score_molecule(r["fragments"])["mw"] == r["module_mass"], r["fragments"]


def test_three_historical_fails_are_retained_with_their_cause():
    fails = [r for r in _returned() if r["verdict"] == "FAIL"]
    assert {tuple(r["fragments"]) for r in fails} == set(HISTORICAL_FAIL) and len(fails) == 3
    for r in fails:
        assert r["mass_abs_error"] == 0.05000000000001137 and r["heavy_atoms_exact"] is True and r["sanitizes"] is True
        assert r["module_mass"] == HISTORICAL_FAIL[tuple(r["fragments"])]
        # cause: the recorded 0.05000000000001137 is the error of the ROUNDED public mw; the unrounded raw sum is within 0.05
        assert abs(_raw(r["fragments"]) - r["reference_mass"]) <= 0.05
