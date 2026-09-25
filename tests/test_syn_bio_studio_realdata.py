"""Module 120 syn_bio_studio: Gillespie mean-field identity vs the two-stage expression
model, damping honesty, and input contracts. Toggle/repressilator architectures are the
published Gardner 2000 / Elowitz-Leibler 2000 motifs (PMIDs 10659857, 10659856)."""
import numpy as np
import pytest
from sugarcode.modules.syn_bio_studio import (compile_circuit, circuit_report,
                                              gillespie_expression, simulate_oscillator,
                                              simulate_toggle)


def test_gillespie_means_match_two_stage_theory():
    # <mRNA> = transcription/mrna_decay = 6.67; <protein> = <mRNA>*translation/protein_decay = 333.3
    r = gillespie_expression(duration=500, seed=1)
    late_m = [x["mrna"] for x in r["trace"] if x["time"] > 100]
    late_p = [x["protein"] for x in r["trace"] if x["time"] > 100]
    assert abs(np.mean(late_m) / (2 / .3) - 1) < 0.15
    assert abs(np.mean(late_p) / (2 / .3 * 5 / .1) - 1) < 0.05  # 330.7 measured


def test_compiler_rejects_unknown_behavior():
    with pytest.raises(ValueError):
        compile_circuit("quantum_entanglement")  # was: silently a "sensor" circuit
    with pytest.raises(ValueError):
        circuit_report("AND")  # was: AND architecture + repressilator simulation


def test_gillespie_zero_propensity_and_duration():
    with pytest.raises(ValueError):
        gillespie_expression(duration=10, transcription=0, seed=1)
    with pytest.raises(ValueError):
        gillespie_expression(duration=0, seed=1)


def test_oscillator_damping_is_reported():
    r = simulate_oscillator()
    assert r["amplitude_first_quarter"] > 3 * r["amplitude_last_quarter"]  # 1.36 vs 0.40
    assert r["sustained_oscillation"] is False
    assert "damped" in r["dynamics_note"]


def test_toggle_bistability_persists():
    r = simulate_toggle()
    assert r["bistable_proxy"] > 0 and r["A"][-1] != r["B"][-1]
