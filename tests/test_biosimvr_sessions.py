"""Regression tests for BUG 59 (measure read the reader, not the plate) and
BUG 60 (run_session molecular_docking crashed on wrong dock() signature)."""
import math
import numpy as np
import pytest
from sugarcode.modules import biosimvr as vr


def test_crispr_session_measures_plate_signal_not_reader():
    s = vr.run_session("crispr_transfection")
    assert any("reporter fluorescence 0.72" in o for o in s["observations"])
    meas = [e for e in s["action_log"] if e["action"] == "measure"]
    assert meas and meas[0]["result"]["reading"] == 0.72  # was 0.0 (reader object has no signal)


def test_docking_session_runs_and_reports_dg():
    s = vr.run_session("molecular_docking")
    assert any("dock dG" in o and "kcal/mol" in o for o in s["observations"])  # was TypeError crash


def test_rotation_is_a_proper_rotation():
    from sugarcode.modules.biosimvr.core import molecular_docking_experiment
    lig = np.array([[0, 0, 0], [1.4, 0, 0]], float)
    pocket = np.array([[0, 0, 0], [6, 0, 0], [0, 6, 0], [0, 0, 6], [6, 6, 0], [6, 0, 6], [0, 6, 6], [6, 6, 6]], float)
    res = molecular_docking_experiment(lig, pocket, steps=20, seed=3)
    pose = np.array(res["optimized_pose_xyz"])
    d = np.linalg.norm(pose[:, None, :] - pocket[None, :, :], axis=2)
    lj = (3 / np.maximum(d, .5)) ** 12 - 2 * (3 / np.maximum(d, .5)) ** 6
    recomp = float(np.sum(np.min(lj, axis=1)) + .02 * np.sum((pose.mean(0) - pocket.mean(0)) ** 2))
    assert abs(recomp - res["score"]) < 1e-6  # returned pose reproduces returned score
    assert math.dist(pose[0], pose[1]) == pytest.approx(1.4, abs=1e-9)  # rigid body: bond length preserved


def test_protocol_sim_deterministic_and_gain_exact():
    protocol = [
        {"action": "pipette", "sample": "a", "volume_uL": 100, "cv": 0.01},
        {"action": "incubate", "sample": "a", "minutes": 120, "temp_C": 37},
        {"action": "measure", "sample": "a"},
    ]
    e1, e2 = vr.run_experiment(protocol, seed=42), vr.run_experiment(protocol, seed=42)
    assert e1["execution_log"] == e2["execution_log"]
    assert len(e1["diagnostics"]) == 51
    expected_gain = 1 - math.exp(-120 / 240)
    assert e1["samples"]["a"]["signal"] == pytest.approx(expected_gain, rel=1e-9)
