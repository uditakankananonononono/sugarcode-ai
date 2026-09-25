"""BUG 56 regression: generations_run must equal the actual simulated
generations, and playground_report diversity must use the final frequency
vector, not a stale every-10-gen snapshot."""
import math
from sugarcode.modules.bioplayground import (run_sandbox, playground_report,
                                             diversity_metrics, ecological_competition)


def test_full_run_counts_generations_exactly():
    r = run_sandbox(pop_size=40000, generations=300, n_alleles=2,
                    fitness=[1.0, 1.0], mutation_rate=0.01, seed=1)
    assert r["generations_run"] == 300 and abs(sum(r["final_freq"]) - 1.0) < 1e-3


def test_gen_one_fixation_reports_one_generation():
    r = run_sandbox(pop_size=200, generations=300, seed=42)
    assert r["fixation_gen"] == 1 and r["generations_run"] == 1


def test_early_loss_metadata_and_final_freq():
    r = run_sandbox(pop_size=100, generations=200, n_alleles=2,
                    fitness=[0.9, 1.0], mutation_rate=0.005, seed=0)
    assert r["fixation_gen"] == 92 and r["generations_run"] == 92
    assert r["final_freq"][0] == 0.0 and r["trajectory_every_10gen"][-1][0] > 0.0


def test_report_diversity_uses_final_freq():
    rep = playground_report([{"fitness": [0.9, 1.0]}, {"fitness": [1.0, 0.95]}])
    ms = rep["environment_sweep"]["most_stable"]["result"]
    assert rep["diversity"] == diversity_metrics(ms["final_freq"])


def test_mutation_equilibrium_matches_theory():
    r = run_sandbox(pop_size=40000, generations=300, n_alleles=2,
                    fitness=[1.0, 1.0], mutation_rate=0.01, seed=1)
    theory = 0.5 + 0.5 * (1 - 2 * 0.01) ** 300  # 0.5012
    assert abs(r["final_construct_freq"] - theory) < 0.02


def test_lv_matches_analytic_logistic_midcourse():
    lv = ecological_competition([0.1], [0.8], [[1.0]], steps=100, dt=0.05)
    analytic = 1.0 / (1.0 + 9.0 * math.exp(-0.8 * 100 * 0.05))  # 0.8585
    assert abs(lv["final"][0] - analytic) < 0.01
