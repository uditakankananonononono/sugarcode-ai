"""Regression tests for behavior at base revision 99cb2d32."""
import tracemalloc

import numpy as np

from sugarcode.modules.molecule_eval import evaluate_library


def _old_pairs(n, max_pairs, seed):
    # the pre-fix algorithm, kept here as the reference for identical draws
    rng = np.random.default_rng(seed)
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    if len(pairs) > max_pairs:
        take = rng.choice(len(pairs), max_pairs, replace=False)
        pairs = [pairs[i] for i in sorted(take)]
    return pairs


def test_pair_sample_is_identical_to_list_based_sample():
    from sugarcode.modules.molecule_eval.core import _iter_pairs  # absent before the fix
    for n, m in [(2, 5), (3, 3), (40, 50), (40, 780), (40, 781), (57, 1000), (200, 10000)]:
        assert list(_iter_pairs(n, m, np.random.default_rng(29))) == _old_pairs(n, m, 29), (n, m)
    assert list(_iter_pairs(0, 5, np.random.default_rng(1))) == []
    assert list(_iter_pairs(1, 5, np.random.default_rng(1))) == []
    assert list(_iter_pairs(50, 0, np.random.default_rng(1))) == []


def _distinct_smiles(k):
    out, i = [], 0
    while len(out) < k:  # chains of C/N/O with one branch: distinct graphs, cheap to fingerprint
        s = "".join("CNO"[(i // 3 ** p) % 3] for p in range(8))
        out.append(s + "C" * (i % 7 + 1) + "(" + "C" * (i // 7 % 5 + 1) + ")" + "N" * (i // 35 % 4 + 1))
        i += 1
    return list(dict.fromkeys(out))


def test_pair_enumeration_memory_is_bounded_by_max_pairs():
    lib = _distinct_smiles(1100)
    tracemalloc.start()
    try:
        r = evaluate_library(lib, max_pairs=100)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert r["methods"]["pair_count"] == 100 and r["unique_graph_count"] > 1000
    # old code built every (i, j) tuple first: ~600k pairs, well over 60 MB
    assert peak < 40e6, peak


def test_stereo_is_reported_by_evaluate_library():
    r = evaluate_library(["CCO", "N[C@@H](C)C(=O)O", "F/C=C/F", "c1ccccc1"])
    assert r["stereo_ignored_count"] == 2
    assert evaluate_library(["CCO"])["stereo_ignored_count"] == 0
    assert any("Stereochemistry" in x for x in r["limitations"])


def test_valence_impossible_input_is_invalid_in_library():
    r = evaluate_library(["CCO", "FC(F)(F)(F)F", "C(C)(C)(C)(C)C"])
    assert r["valid_count"] == 1 and r["invalid_count"] == 2
