"""rna_nussinov: Nussinov-Jacobson 1980 maximum base-pair folding.

Hand-computed fixtures on small RNAs, plus an exhaustive brute-force verifier
(independent backtracking over compatible pair sets, no DP) on short random
sequences: same max pair count, same exact optimal-structure count, same set
of optimal structures, and the traceback structure is one of them.
"""
import random

import pytest

from sugarcode.modules.rna_nussinov import (
    brute_force, dot_bracket_to_pairs, evaluate_structure, fold, normalize_sequence,
    optimal_structures, pairs_to_dot_bracket, structure_stats)

# (sequence, min_loop, allow_gu, hand max pairs, hand structure, hand optimal count)
HAND = [
    ("", 3, True, 0, "", 1),
    ("AAAA", 3, True, 0, "....", 1),
    ("GC", 0, True, 1, "()", 1),
    ("GC", 3, True, 0, "..", 1),
    ("GCGC", 0, True, 2, None, 2),                 # ()() and (())
    ("GGGAAACCC", 3, True, 3, "(((...)))", 1),
    ("GGGGAAAACCCC", 3, True, 4, "((((....))))", 1),
    ("GAAAU", 3, True, 1, "(...)", 1),              # G-U wobble
    ("GAAAU", 3, False, 0, ".....", 1),
    ("GGGAAACCCAGGGAAACCC", 3, True, 6, "(((...))).(((...)))", 1),
]


@pytest.mark.parametrize("seq,ml,gu,mp,db,count", HAND)
def test_hand_fixtures(seq, ml, gu, mp, db, count):
    r = fold(seq, min_loop=ml, allow_gu=gu)
    assert r["max_pairs"] == mp == r["stats"]["pair_count"]
    if db is not None:
        assert r["dot_bracket"] == db
    assert r["optimal_structure_count"] == count
    assert evaluate_structure(seq, r["dot_bracket"], min_loop=ml, allow_gu=gu)["valid"]


def test_hand_enumerated_min_loop_4():
    # GGGAAACCC with min_loop 4: G2-C6 closes only 3 bases, so the max is 2 pairs.
    # By hand: inner pair (b,d) needs d-b-1 >= 4 -> (1,6),(1,7),(2,7); outer pair
    # (a,c) must enclose it -> 2 + 1 + 2 = 5 optimal structures.
    expected = {"((....)).", "((....).)", "((.....))", "(.(....))", ".((....))"}
    r = fold("GGGAAACCC", min_loop=4)
    assert r["max_pairs"] == 2 and r["optimal_structure_count"] == 5
    assert set(optimal_structures("GGGAAACCC", min_loop=4)) == expected
    assert r["dot_bracket"] == ".((....))"        # tie-break: leave i unpaired first


def test_hand_stats_two_hairpins():
    s = fold("GGGAAACCCAGGGAAACCC")["stats"]
    assert s == {"length": 19, "pair_count": 6, "paired_bases": 12, "unpaired_bases": 7,
                 "paired_fraction": 12 / 19, "pair_types": {"GC": 6, "AU": 0, "GU": 0},
                 "stem_count": 2, "stem_lengths": [3, 3], "hairpin_count": 2,
                 "max_nesting_depth": 3}
    r = fold("GGGAAACCCAGGGAAACCC")
    assert r["pairs"] == [[0, 8], [1, 7], [2, 6], [10, 18], [11, 17], [12, 16]]
    assert r["pairs_1based"][0] == [1, 9]


def test_brute_force_verifier_random_short():
    rng = random.Random(20260924)
    for _ in range(250):
        n = rng.randint(0, 13)
        seq = "".join(rng.choice("ACGU") for _ in range(n))
        ml, gu = rng.randint(0, 4), rng.random() < 0.5
        r = fold(seq, min_loop=ml, allow_gu=gu)
        b = brute_force(seq, min_loop=ml, allow_gu=gu)
        assert r["max_pairs"] == b["max_pairs"], seq
        assert r["optimal_structure_count"] == len(b["optimal_structures"]), seq
        assert optimal_structures(seq, min_loop=ml, allow_gu=gu) == b["optimal_structures"], seq
        assert r["dot_bracket"] in b["optimal_structures"]


def test_brute_force_verifier_structured_16mer():
    seq = "GGACUUCGGUCCAGCU"
    for ml in (0, 3):
        r, b = fold(seq, min_loop=ml), brute_force(seq, min_loop=ml)
        assert r["max_pairs"] == b["max_pairs"]
        assert r["optimal_structure_count"] == len(b["optimal_structures"])


def test_agrees_with_independent_riboswitch_implementation():
    from sugarcode.modules.riboswitch import nussinov_fold
    rng = random.Random(7)
    for _ in range(40):
        seq = "".join(rng.choice("ACGU") for _ in range(rng.randint(2, 60)))
        assert fold(seq)["max_pairs"] == nussinov_fold(seq)["pair_count"]


def test_min_loop_is_respected_in_traceback():
    rng = random.Random(3)
    for _ in range(15):
        seq = "".join(rng.choice("ACGU") for _ in range(80))
        for ml in (0, 3, 5):
            r = fold(seq, min_loop=ml, count_optimal=False)
            assert all(j - i - 1 >= ml for i, j in r["pairs"])
            assert evaluate_structure(seq, r["dot_bracket"], min_loop=ml)["valid"]


def test_dot_bracket_roundtrip_and_errors():
    pairs = [(0, 8), (1, 7), (2, 6)]
    assert dot_bracket_to_pairs(pairs_to_dot_bracket(pairs, 9)) == pairs
    for bad in ("(()", "())", "(.x)"):
        with pytest.raises(ValueError):
            dot_bracket_to_pairs(bad)


def test_evaluate_structure_reports_violations():
    r = evaluate_structure("GAAAA", "(...)")
    assert not r["valid"] and "not an allowed pair" in r["violations"][0]["reason"]
    r = evaluate_structure("GAC", "(.)", min_loop=3)
    assert not r["valid"] and "min_loop" in r["violations"][0]["reason"]


def test_input_handling():
    assert normalize_sequence(" ggg aaa ccc ") == "GGGAAACCC"
    assert fold("GGGAAATTT".replace("T", "C"))["dot_bracket"] == "(((...)))"
    assert fold("GGGTTTCCC")["sequence"] == "GGGUUUCCC"   # T read as U
    with pytest.raises(ValueError):
        fold("GGGNCCC")
    with pytest.raises(ValueError):
        fold("GGGAAACCC", min_loop=-1)
    with pytest.raises(ValueError):
        fold("A" * 50, max_length=40)
    with pytest.raises(ValueError):
        brute_force("A" * 21)


def test_long_sequence_runs_without_counting():
    rng = random.Random(11)
    seq = "".join(rng.choice("ACGU") for _ in range(500))
    r = fold(seq)
    assert r["optimal_structure_count"] is None
    assert r["max_pairs"] == len(r["pairs"]) and len(r["dot_bracket"]) == 500


def test_structure_stats_counts_pair_types():
    s = structure_stats("GAAAUCAAAG", [(0, 4), (5, 9)])
    assert s["pair_types"] == {"GC": 1, "AU": 0, "GU": 1} and s["hairpin_count"] == 2


def test_registered():
    from omega.registry import REGISTRY
    assert REGISTRY["rna_nussinov"].subnetwork == "synthetic-biology"
