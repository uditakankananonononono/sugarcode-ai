"""profile_hmm: Durbin et al. 1998 Ch. 5 profile HMM construction, Viterbi, Forward.

Hand-computed fixtures on tiny models (exact fractions), plus an independent
brute-force verifier that enumerates every state path (no DP) and must agree
with Viterbi (max) and Forward (sum) on random small alignments.
"""
import math
import random
from fractions import Fraction as F

import numpy as np
import pytest

from sugarcode.modules.profile_hmm import brute_force, build_profile_hmm, forward, viterbi


@pytest.fixture
def tiny():
    # AC, AC, AG: 2 match columns, no gaps, Laplace pseudocounts.
    return build_profile_hmm(["AC", "AC", "AG"])


def test_hand_construction_tiny(tiny):
    m = tiny
    assert m.length == 2 and m.alphabet == "ACGT" and m.consensus() == "AC"
    # M1 emissions: A 3+1 of 3+4 -> 4/7, others 1/7; M2: C 3/7, G 2/7, A,T 1/7
    assert np.allclose(m.match_emissions[1], [4 / 7, 1 / 7, 1 / 7, 1 / 7])
    assert np.allclose(m.match_emissions[2], [1 / 7, 3 / 7, 2 / 7, 1 / 7])
    # Begin and M1: 3 counts to next M, +1 on each of 3 transitions -> 4/6, 1/6, 1/6
    assert np.allclose(m.t_match[0], [4 / 6, 1 / 6, 1 / 6])
    assert np.allclose(m.t_match[1], [4 / 6, 1 / 6, 1 / 6])
    # M2 (last): End 3+1, I2 0+1, no D3 -> 4/5, 1/5, 0
    assert np.allclose(m.t_match[2], [4 / 5, 1 / 5, 0])
    # unseen I/D states: uniform over existing transitions
    assert np.allclose(m.t_insert[0], [1 / 3] * 3) and np.allclose(m.t_insert[2], [1 / 2, 1 / 2, 0])
    assert np.allclose(m.t_delete[1], [1 / 3] * 3) and np.allclose(m.t_delete[2], [1 / 2, 1 / 2, 0])
    assert np.allclose(m.insert_emissions, 1 / 4)


def test_hand_viterbi_and_forward_AC(tiny):
    v = viterbi(tiny, "AC")
    # B->M1(A)->M2(C)->E = 4/6 * 4/7 * 4/6 * 3/7 * 4/5 = 64/735
    assert v["state_path"] == ["M1", "M2"]
    assert math.isclose(math.exp(v["log_prob"]), 64 / 735, rel_tol=1e-12)
    assert math.isclose(v["bits"], math.log2(64 / 735), rel_tol=1e-12)
    # log-odds vs uniform background: 64/735 / (1/4)^2
    assert math.isclose(v["log_odds"], math.log((64 / 735) * 16), rel_tol=1e-12)
    f, b = forward(tiny, "AC"), brute_force(tiny, "AC")
    assert b["path_count"] == 13
    assert math.isclose(math.exp(f["log_prob"]), b["forward_prob"], rel_tol=1e-12)


def test_hand_forward_single_residue(tiny):
    # All five paths that emit exactly "A" (derived by hand):
    paths = [F(4, 6) * F(4, 7) * F(1, 6) * F(1, 2),                  # B M1(A) D2 E
             F(1, 6) * F(1, 3) * F(1, 7) * F(4, 5),                  # B D1 M2(A) E
             F(1, 6) * F(1, 4) * F(1, 3) * F(1, 3) * F(1, 2),        # B I0(A) D1 D2 E
             F(1, 6) * F(1, 3) * F(1, 4) * F(1, 3) * F(1, 2),        # B D1 I1(A) D2 E
             F(1, 6) * F(1, 3) * F(1, 2) * F(1, 4) * F(1, 2)]        # B D1 D2 I2(A) E
    v, f = viterbi(tiny, "A"), forward(tiny, "A")
    assert v["state_path"] == ["M1", "D2"]
    assert math.isclose(math.exp(v["log_prob"]), float(max(paths)), rel_tol=1e-12)
    assert math.isclose(math.exp(f["log_prob"]), float(sum(paths)), rel_tol=1e-12)
    assert brute_force(tiny, "A")["path_count"] == 5


def test_hand_insert_column_construction():
    # column 2 is 3/4 gaps -> insert column; one sequence visits I1 emitting G.
    m = build_profile_hmm(["A-C", "AGC", "A-C", "A-C"])
    assert m.match_columns == [0, 2] and m.length == 2
    assert np.allclose(m.t_match[1], [(3 + 1) / 7, (1 + 1) / 7, 1 / 7])
    assert np.allclose(m.t_insert[1], [(1 + 1) / 4, 1 / 4, 1 / 4])
    assert np.allclose(m.insert_emissions[1], [1 / 5, 1 / 5, 2 / 5, 1 / 5])
    v = viterbi(m, "AGC")
    assert v["state_path"] == ["M1", "I1", "M2"]
    assert [a["residue"] for a in v["alignment"]] == ["A", "G", "C"]


def test_hand_delete_path():
    # column 0 is exactly half gaps -> still a match column (threshold: > half = insert)
    m = build_profile_hmm(["AC", "-C"])
    assert m.match_columns == [0, 1]
    assert np.allclose(m.t_match[0], [(1 + 1) / 5, 1 / 5, (1 + 1) / 5])
    assert viterbi(m, "C")["state_path"] == ["D1", "M2"]
    assert viterbi(m, "C")["alignment"][0] == {"state": "D1", "residue": "-", "position": None}


def test_model_is_normalised():
    rng = random.Random(1)
    for _ in range(30):
        aln = ["".join(rng.choice("ACGT--") for _ in range(8)) for _ in range(5)]
        try:
            m = build_profile_hmm(aln, alphabet="ACGT")
        except ValueError:
            continue
        assert np.allclose(m.match_emissions[1:].sum(axis=1), 1)
        assert np.allclose(m.insert_emissions.sum(axis=1), 1)
        assert np.allclose(m.t_match.sum(axis=1), 1) and np.allclose(m.t_insert.sum(axis=1), 1)
        assert np.allclose(m.t_delete[1:].sum(axis=1), 1)
        assert m.t_match[-1][2] == m.t_insert[-1][2] == m.t_delete[-1][2] == 0


def test_brute_force_verifier_random_models():
    rng = random.Random(20260924)
    checked = 0
    for _ in range(200):
        aln = ["".join(rng.choice("ACGT-") for _ in range(rng.randint(1, 4)))] 
        width = len(aln[0])
        aln += ["".join(rng.choice("ACGT-") for _ in range(width)) for _ in range(rng.randint(0, 3))]
        try:
            m = build_profile_hmm(aln, alphabet="ACGT", gap_threshold=rng.choice([0.0, 0.5, 0.9]),
                                  pseudocount=rng.choice([0.5, 1.0, 2.0]),
                                  insert_emissions=rng.choice(["counted", "background"]))
        except ValueError:
            continue
        seq = "".join(rng.choice("ACGT") for _ in range(rng.randint(0, 4)))
        v, f, b = viterbi(m, seq), forward(m, seq), brute_force(m, seq)
        assert math.isclose(math.exp(v["log_prob"]), b["viterbi_prob"], rel_tol=1e-9)
        assert math.isclose(math.exp(f["log_prob"]), b["forward_prob"], rel_tol=1e-9)
        assert v["state_path"] == b["best_path"] or math.isclose(
            b["viterbi_prob"], _path_prob(m, seq, v["state_path"]), rel_tol=1e-9)
        checked += 1
    assert checked > 100


def _path_prob(m, seq, states):
    p, prev, i = 1.0, ("B", 0), 0
    x = m.encode(seq)
    for s in states:
        kind, k = s[0], int(s[1:])
        p *= m.transition(prev, (kind, k))
        if kind == "M":
            p *= m.match_emissions[k][x[i]]; i += 1
        elif kind == "I":
            p *= m.insert_emissions[k][x[i]]; i += 1
        prev = (kind, k)
    return p * m.transition(prev, ("E", 0))


def test_viterbi_path_probability_matches_score():
    m = build_profile_hmm(["ACGT-A", "ACG-TA", "AC-GTA", "ACGTTA"])
    for s in ["ACGTA", "AGTA", "ACGTTTA", "A"]:
        v = viterbi(m, s)
        assert math.isclose(math.exp(v["log_prob"]), _path_prob(m, s, v["state_path"]), rel_tol=1e-9)
        assert forward(m, s)["log_prob"] >= v["log_prob"]


def test_family_member_outscores_unrelated():
    fam = ["HEAGAWGHEE", "HEAGAW-HEE", "HDAGAWGHEE", "HEAG-WGHEE"]
    m = build_profile_hmm(fam)
    assert m.alphabet.startswith("ACDEF")
    assert forward(m, "HEAGAWGHEE")["log_odds"] > 0 > forward(m, "PPPPPPPPPP")["log_odds"]


def test_options_and_errors():
    m = build_profile_hmm(["AC-", "ACG"], match_columns=[0, 1, 2])
    assert m.length == 3
    m = build_profile_hmm(["ACGU", "ACGU"])
    assert m.alphabet == "ACGU" and viterbi(m, "ACGT")["state_path"] == ["M1", "M2", "M3", "M4"]
    m = build_profile_hmm(["AC", "AG"], background={"A": .4, "C": .1, "G": .1, "T": .4})
    assert np.allclose(m.background, [.4, .1, .1, .4])
    for bad in ([], ["AC", "A"], ["--", "--"]):
        with pytest.raises(ValueError):
            build_profile_hmm(bad, alphabet="ACGT")
    with pytest.raises(ValueError):
        build_profile_hmm(["AC", "AC"], insert_emissions="other")
    with pytest.raises(ValueError):
        viterbi(build_profile_hmm(["AC", "AC"]), "AXC")
    d = build_profile_hmm(["AC", "AC"]).to_dict()
    assert d["consensus"] == "AC" and len(d["match_emissions"]) == 2


def test_registered():
    from omega.registry import REGISTRY
    assert REGISTRY["profile_hmm"].subnetwork == "protein-engineering"
