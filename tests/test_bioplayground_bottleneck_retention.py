"""Rows S5-008.A01.C04 + S5-008.A02: scheduled bottlenecks must still fire
when the construct fixates or is lost before bottleneck_at, and the
interpretation string must not claim loss or a fitness cost the run did
not show."""
from sugarcode.modules.bioplayground import run_sandbox


def test_bottleneck_fires_after_construct_fixed():
    r = run_sandbox(pop_size=200, generations=300, bottleneck_at=150, seed=42)
    assert r["fixation_gen"] == 1  # construct fixes immediately, run must not stop there
    assert any(e["event"] == "bottleneck" and e["gen"] == 150 for e in r["events"])
    assert r["generations_run"] >= 150


def test_bottleneck_fires_after_construct_lost():
    r = run_sandbox(pop_size=100, generations=200, n_alleles=2, fitness=[0.9, 1.0],
                    mutation_rate=0.005, seed=0, bottleneck_at=150)
    assert r["fixation_gen"] == 92  # construct lost at gen 92, run must not stop there
    assert any(e["event"] == "bottleneck" and e["gen"] == 150 for e in r["events"])
    assert r["generations_run"] == 200


def test_no_fixation_early_stop_without_pending_bottleneck():
    # existing pinned behavior: no bottleneck scheduled -> stop at fixation
    r = run_sandbox(pop_size=200, generations=300, seed=42)
    assert r["generations_run"] == 1


def test_mid_frequency_run_reports_no_loss_and_no_fitness_cost():
    # neutral fitness, construct ends at 0.37: not lost, and neutral fitness
    # cannot support a "fitness cost" verdict
    r = run_sandbox(pop_size=100, generations=200, n_alleles=2, fitness=[1.0, 1.0],
                    mutation_rate=0.005, seed=42)
    assert 0.0 < r["final_construct_freq"] <= 0.5
    assert "lost" not in r["interpretation"].lower()
    assert "fitness cost" not in r["interpretation"].lower()


def test_advantaged_branch_states_endpoint_not_stability():
    # construct fitness advantage + final frequency > 0.5 must still be
    # reported as one sampled endpoint with supplied relative fitness,
    # not as a stability or selection-coefficient claim
    r = run_sandbox(pop_size=300, generations=200, fitness=[1.02, 0.98, 0.98], seed=5)
    assert r["final_construct_freq"] > 0.5
    interp = r["interpretation"].lower()
    assert "stable" not in interp
    assert "holds it against drift" not in interp
    assert "selection coefficient" not in interp
    assert "final frequency" in interp
    assert "relative fitness" in interp


def test_loss_wording_only_when_recorded_event_is_loss():
    # seed 14: construct fixes at gen 1, bottleneck at 150, final frequency 0.0 -
    # the recorded endpoint event is a fixation, so the interpretation must not
    # report gen 1 as a loss generation
    r = run_sandbox(pop_size=100, generations=200, n_alleles=2, fitness=[0.9, 1.0],
                    mutation_rate=0.005, seed=14, bottleneck_at=150)
    assert any(e["event"] == "construct_fixed" and e["gen"] == 1 for e in r["events"])
    assert any(e["event"] == "bottleneck" and e["gen"] == 150 for e in r["events"])
    assert r["final_construct_freq"] == 0.0
    interp = r["interpretation"].lower()
    assert "sampled loss at gen 1" not in interp
    assert "loss" not in interp.split("fixation")[0]
    assert "fixation at gen 1" in interp
