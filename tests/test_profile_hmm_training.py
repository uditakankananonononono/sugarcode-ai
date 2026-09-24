"""profile_hmm Baum-Welch: hand-computed E/M steps on a tiny model, exact
posterior counts from brute-force path enumeration, EM monotonicity,
convergence and held-out reporting."""
import math
import random

import numpy as np
import pytest

from sugarcode.modules.profile_hmm import (
    ProfileHMM, baum_welch, brute_force_expected_counts, brute_force_paths,
    build_profile_hmm, expected_counts, log_likelihood, maximize, random_profile_hmm)


@pytest.fixture
def tiny():
    # L = 1, alphabet {A, B}. Hand-set parameters.
    return ProfileHMM(
        "AB", 1,
        match_emissions=np.array([[0, 0], [0.75, 0.25]]),
        insert_emissions=np.array([[0.5, 0.5], [0.5, 0.5]]),
        t_match=np.array([[0.5, 0.25, 0.25], [0.5, 0.5, 0]]),    # Begin; M1 -> End/I1
        t_insert=np.array([[0.5, 0.25, 0.25], [0.5, 0.5, 0]]),
        t_delete=np.array([[0, 0, 0], [0.5, 0.5, 0]]),
        background=np.array([0.5, 0.5]), match_columns=[0])


def test_hand_e_step(tiny):
    # Paths emitting "A":  B M1(A) E     = .5*.75*.5       = 3/16
    #                      B I0(A) D1 E  = .25*.5*.25*.5   = 1/64
    #                      B D1 I1(A) E  = .25*.5*.5*.5    = 1/32
    # P(A) = 15/64; posteriors 4/5, 1/15, 2/15.
    paths = dict((tuple(p), q) for p, q in brute_force_paths(tiny, "A"))
    assert paths == pytest.approx({("M1",): 3 / 16, ("I0", "D1"): 1 / 64, ("D1", "I1"): 1 / 32})
    c, ll = expected_counts(tiny, ["A"])
    assert math.isclose(ll, math.log(15 / 64), rel_tol=1e-12)
    assert np.allclose(c["match_emissions"][1], [4 / 5, 0])
    assert np.allclose(c["insert_emissions"], [[1 / 15, 0], [2 / 15, 0]])
    assert np.allclose(c["t_match"], [[4 / 5, 1 / 15, 2 / 15], [4 / 5, 0, 0]])
    assert np.allclose(c["t_insert"], [[0, 0, 1 / 15], [2 / 15, 0, 0]])
    assert np.allclose(c["t_delete"][1], [1 / 15, 2 / 15, 0])


def test_hand_m_step_ml(tiny):
    c, _ = expected_counts(tiny, ["A"])
    m = maximize(tiny, c, pseudocount=0)
    assert np.allclose(m.t_match, [[4 / 5, 1 / 15, 2 / 15], [1, 0, 0]])
    assert np.allclose(m.t_insert[0], [0, 0, 1]) and np.allclose(m.t_insert[1], [1, 0, 0])
    assert np.allclose(m.t_delete[1], [1 / 3, 2 / 3, 0])
    assert np.allclose(m.match_emissions[1], [1, 0])
    # new P(A) = 4/5 + 1/15*1/3 + 2/15*2/3 = 41/45 (up from 15/64)
    assert math.isclose(math.exp(log_likelihood(m, ["A"])), 41 / 45, rel_tol=1e-12)


def test_hand_m_step_pseudocount(tiny):
    c, _ = expected_counts(tiny, ["A"])
    m = maximize(tiny, c, pseudocount=1)
    # Begin row: (4/5+1, 1/15+1, 2/15+1) / 4
    assert np.allclose(m.t_match[0], [1.8 / 4, (16 / 15) / 4, (17 / 15) / 4])
    # last-position rows normalise over the 2 existing transitions only
    assert np.allclose(m.t_match[1], [1.8 / 2.8, 1 / 2.8, 0])
    assert np.allclose(m.match_emissions[1], [1.8 / 2.8, 1 / 2.8])


def test_e_step_matches_brute_force_posterior_counts():
    rng = random.Random(20260924)
    for _ in range(60):
        m = random_profile_hmm(rng.randint(1, 3), "ACGT", seed=rng.randint(0, 10 ** 6))
        seqs = ["".join(rng.choice("ACGT") for _ in range(rng.randint(0, 3)))
                for _ in range(rng.randint(1, 3))]
        c, ll = expected_counts(m, seqs)
        b = brute_force_expected_counts(m, seqs)
        for key in c:
            assert np.allclose(c[key], b[key], atol=1e-12), key
        assert math.isclose(ll, log_likelihood(m, seqs), rel_tol=1e-9)


def test_e_step_on_alignment_built_model_matches_brute_force():
    m = build_profile_hmm(["ACG", "A-G", "ACC"])
    seqs = ["ACG", "AG", "ACCG"]
    c, _ = expected_counts(m, seqs)
    b = brute_force_expected_counts(m, seqs)
    for key in c:
        assert np.allclose(c[key], b[key], atol=1e-12)


FAMILY = ["ACGTAC", "ACGAC", "ACGTTAC", "AGTAC", "ACGTAC", "ACGTAG"]


def test_ml_em_log_likelihood_never_decreases_and_converges():
    m0 = random_profile_hmm(5, "ACGT", seed=1)
    m, rep = baum_welch(m0, FAMILY, pseudocount=0, max_iter=300, tol=1e-6)
    lls = [h["train_log_likelihood"] for h in rep["history"]]
    assert all(b >= a - 1e-9 for a, b in zip(lls, lls[1:]))
    assert rep["converged"] and rep["iterations"] < 300
    assert abs(lls[-1] - lls[-2]) < 1e-6 and lls[-1] > lls[0] + 10


def test_map_em_objective_never_decreases():
    m0 = random_profile_hmm(5, "ACGT", seed=2)
    m, rep = baum_welch(m0, FAMILY, pseudocount=1.0, max_iter=200)
    obj = [h["objective"] for h in rep["history"]]
    assert all(b >= a - 1e-9 for a, b in zip(obj, obj[1:]))
    assert rep["converged"]


def test_heldout_reporting():
    m0 = build_profile_hmm(["ACGTAC", "ACG-AC", "ACGTAC"])
    held = ["ACGTAC", "ACTAC", "GGGGGG"]
    m, rep = baum_welch(m0, FAMILY, heldout=held, pseudocount=1.0, max_iter=50)
    h = rep["history"]
    assert all("heldout_log_likelihood" in e for e in h)
    assert math.isclose(rep["final_heldout_log_likelihood"], log_likelihood(m, held), rel_tol=1e-12)
    n_res = sum(map(len, held))
    assert math.isclose(rep["final_heldout_per_residue"], rep["final_heldout_log_likelihood"] / n_res)
    assert h[0]["iteration"] == 0 and math.isclose(h[0]["heldout_log_likelihood"], log_likelihood(m0, held))
    assert math.isfinite(rep["final_heldout_log_likelihood"])     # pseudocounts keep it finite


def test_training_recovers_family_signal():
    m0 = random_profile_hmm(6, "ACGT", seed=7)
    m, _ = baum_welch(m0, ["ACGTAC"] * 5 + ["ACGAAC", "ACTTAC"], pseudocount=0.1, max_iter=200)
    assert m.consensus() == "ACGTAC"
    assert log_likelihood(m, ["ACGTAC"]) > log_likelihood(m, ["TGCATG"]) + 5


def test_trained_model_stays_normalised_and_masked():
    m, _ = baum_welch(random_profile_hmm(4, "ACGT", seed=3), FAMILY, max_iter=10)
    assert np.allclose(m.match_emissions[1:].sum(axis=1), 1)
    assert np.allclose(m.insert_emissions.sum(axis=1), 1)
    assert np.allclose(m.t_match.sum(axis=1), 1) and np.allclose(m.t_insert.sum(axis=1), 1)
    assert np.allclose(m.t_delete[1:].sum(axis=1), 1)
    assert m.t_match[-1][2] == m.t_insert[-1][2] == m.t_delete[-1][2] == 0


def test_fixed_insert_emissions_option():
    m0 = build_profile_hmm(["ACGT", "ACGT"], insert_emissions="background")
    m, _ = baum_welch(m0, ["ACGTT", "ACGGT"], update_insert_emissions=False, max_iter=5)
    assert np.allclose(m.insert_emissions, m0.insert_emissions)


def test_random_model_is_seeded_and_valid():
    a, b = random_profile_hmm(3, seed=11), random_profile_hmm(3, seed=11)
    assert np.array_equal(a.t_match, b.t_match) and np.array_equal(a.match_emissions, b.match_emissions)
    assert np.allclose(a.t_delete[1:].sum(axis=1), 1) and a.t_match[-1][2] == 0


def test_errors(tiny):
    with pytest.raises(ValueError):
        baum_welch(tiny, [])
    with pytest.raises(ValueError):
        maximize(tiny, expected_counts(tiny, ["A"])[0], pseudocount=-1)
    zero = maximize(tiny, expected_counts(tiny, ["A"])[0], pseudocount=0)
    with pytest.raises(ValueError):
        expected_counts(zero, ["B"])            # impossible under the ML model
    with pytest.raises(ValueError):
        random_profile_hmm(0)
