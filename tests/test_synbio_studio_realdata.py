"""Module 121 synbio_studio: Hill-kinetic circuit contracts, recalibrated repressilator,
and silent-fallback rejection. Motif anchors: Gardner 2000 (PMID 10659857),
Elowitz-Leibler 2000 (PMID 10659856)."""
import numpy as np
import pytest
from sugarcode.modules.synbio_studio import (Circuit, Gate, simulate, logic_verify,
                                             repressilator, toggle_switch, and_gate)


def test_and_gate_truth_table_matches_logic():
    rows = logic_verify(and_gate(), ["AraC", "AHL"], "GFP")["truth_table"]
    got = {(r["inputs"]["AraC"], r["inputs"]["AHL"]): r["output"] for r in rows}
    assert got == {("LOW", "LOW"): "LOW", ("LOW", "HIGH"): "LOW",
                   ("HIGH", "LOW"): "LOW", ("HIGH", "HIGH"): "HIGH"}
    hi = [r["output_level"] for r in rows if r["output"] == "HIGH"][0]
    assert abs(hi - (0.01 + 1.0 * (36 / 37) ** 2) / 0.2) < 0.05  # 4.783 measured


def test_toggle_bistable_from_asymmetric_start():
    r = simulate(toggle_switch(), (0, 200), y0=[1.0, 0.0], n_points=100)
    assert r["steady_state"]["A"] > 7.0 and r["steady_state"]["B"] < 0.1


def test_repressilator_now_oscillates():
    r = simulate(repressilator(), (0, 300), y0=[1.0, 0.0, 0.0], n_points=1200)
    assert r["oscillating"] is True
    assert r["amplitude_last_quarter"]["LacI"] > 2.0  # 2.77 measured; was 0.002 at n=2.1


def test_unknown_mode_logic_regulator_rejected():
    with pytest.raises(ValueError):
        simulate(Circuit(gates=[Gate("X", [("R", "block")])]), (0, 10), external={"R": 1.0}, n_points=10)
    with pytest.raises(ValueError):
        simulate(Circuit(gates=[Gate("X", [("A", "activate")], logic="NAND")]),
                 (0, 10), external={"A": 1.0}, n_points=10)
    with pytest.raises(KeyError):
        # was: ghost repressor silently 0 -> full expression (steady 5.05)
        simulate(Circuit(gates=[Gate("X", [("ghost", "repress")])]), (0, 10), n_points=10)


def test_demo_constructors_exported_and_named():
    assert repressilator().name == "repressilator"
    assert toggle_switch().name == "toggle_switch"
    assert and_gate().name == "and_gate"
