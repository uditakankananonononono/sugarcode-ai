"""bio.phylo phylogenetics toolkit (drop 78)."""
import math

import pytest

from sugarcode.bio import phylo as ph
from sugarcode.bio.newick import parse_newick, write_newick


def test_p_distance_and_pairwise_deletion():
    assert ph.p_distance("ACGT", "ACGA") == pytest.approx(0.25)
    # gap/ambiguous columns dropped for the pair: 2 comparable sites, 0 diffs
    assert ph.p_distance("ACGT", "A-GN") == 0.0
    with pytest.raises(ValueError):
        ph.p_distance("ACGT", "ACG")      # unequal alignment lengths
    with pytest.raises(ValueError):
        ph.p_distance("----", "....")     # nothing comparable


def test_jc69_hand_computed_and_saturation():
    d = ph.jc69_distance("AAAAAAAAAA", "AAAAAAAAGA")  # p = 0.1
    assert d == pytest.approx(-0.75 * math.log(1 - 0.4 / 3))
    assert ph.jc69_distance("AAAAAAAAAA", "CCCCCCCCAA") == math.inf  # p=.8


def test_k80_hand_computed_and_ts_tv_split():
    # 20 sites: 2 transitions (A->G), 1 transversion (A->C): P=.1, Q=.05
    d = ph.k80_distance("A" * 20, "GG" + "C" + "A" * 17)
    assert d == pytest.approx(-0.5 * math.log(0.75) - 0.25 * math.log(0.9))
    # transitions and transversions are weighted differently
    ts_only = ph.k80_distance("AAAAAAAA", "AGGAAAAA")  # P=.25, Q=0
    tv_only = ph.k80_distance("AAAAAAAA", "ACCAAAAA")  # P=0, Q=.25
    assert ts_only == pytest.approx(-0.5 * math.log(0.5))
    assert tv_only == pytest.approx(-0.5 * math.log(0.75) - 0.25 * math.log(0.5))
    assert ts_only != pytest.approx(tv_only)
    with pytest.raises(ValueError):
        ph.distance_matrix({"a": "AA", "b": "AA"}, "jc85")


def test_distance_matrix_shape():
    dm = ph.distance_matrix({"x": "AAAA", "y": "AAAT", "z": "AATT"},
                            "pdistance")
    assert dm["names"] == ["x", "y", "z"]
    m = dm["matrix"]
    assert all(m[i][i] == 0.0 for i in range(3))
    assert m[0][1] == pytest.approx(0.25) and m[1][0] == m[0][1]
    assert m[0][2] == pytest.approx(0.5)


def _cophon_matches(tree, names, matrix):
    co = ph.cophenetic(tree)
    idx = {x: i for i, x in enumerate(co["names"])}
    for i, a in enumerate(names):
        for j, b in enumerate(names):
            assert co["matrix"][idx[a]][idx[b]] == \
                pytest.approx(matrix[i][j])


def test_upgma_exact_small_matrix():
    m = [[0, 2, 6], [2, 0, 6], [6, 6, 0]]
    t = ph.upgma(["A", "B", "C"], m)
    # A,B join at height 1; C at height 3; total length 1+1+2+3 = 7
    assert ph.total_branch_length(t) == pytest.approx(7.0)
    _cophon_matches(t, ["A", "B", "C"], m)  # ultrametric -> exact roundtrip
    with pytest.raises(ValueError):
        ph.upgma(["A"], [[0]])


def test_upgma_ties_deterministic():
    m = [[0, 4, 4], [4, 0, 4], [4, 4, 0]]
    t = ph.upgma(["A", "B", "C"], m)
    t2 = ph.upgma(["A", "B", "C"], m)
    assert write_newick(t) == write_newick(t2)
    assert sorted(ph._nw.leaves(t)) == ["A", "B", "C"]


def test_nj_recovers_additive_tree():
    # true tree ((A:1,B:2):3,(C:2,D:1):2) -> exact distance matrix
    m = [[0, 3, 6, 5], [3, 0, 7, 6], [6, 7, 0, 3], [5, 6, 3, 0]]
    t = ph.neighbor_joining(["A", "B", "C", "D"], m)
    _cophon_matches(t, ["A", "B", "C", "D"], m)  # NJ exact on additive data


def test_nj_two_taxa_and_validation():
    t = ph.neighbor_joining(["A", "B"], [[0, 5], [5, 0]])
    assert [c["length"] for c in t["children"]] == [2.5, 2.5]
    with pytest.raises(ValueError):
        ph.neighbor_joining(["A"], [[0]])
    with pytest.raises(ValueError):
        ph.build_tree(["A", "B"], [[0, 1], [1, 0]], "ml")


def test_nj_negative_branches_kept():
    # non-additive input: NJ may produce negative limbs - documented, kept
    seqs = {"A": "AAAAAAAAAA", "B": "AAAAAAAAGA", "C": "AACAAACAGC"}
    dm = ph.distance_matrix(seqs, "jc69")
    t = ph.neighbor_joining(dm["names"], dm["matrix"])
    lengths = [n["length"] for n in ph._nw.preorder(t)
               if n["length"] is not None]
    assert any(x < 0 for x in lengths)


def test_cophenetic_and_total_length_on_parsed_tree():
    t = parse_newick("(A:1,(B:2,C:3):4);")
    co = ph.cophenetic(t)
    i = {x: k for k, x in enumerate(co["names"])}
    assert co["matrix"][i["B"]][i["C"]] == pytest.approx(5.0)
    assert co["matrix"][i["A"]][i["B"]] == pytest.approx(7.0)
    assert co["matrix"][i["A"]][i["C"]] == pytest.approx(8.0)
    assert ph.total_branch_length(t) == pytest.approx(10.0)


def test_end_to_end_alignment_to_newick_roundtrip():
    seqs = {"human": "ACGTACGTAC", "chimp": "ACGTACGTAT",
            "mouse": "ACGAACGAAC", "rat": "ACGAACGAAA"}
    dm = ph.distance_matrix(seqs, "k80")
    for method in ("upgma", "nj"):
        t = ph.build_tree(dm["names"], dm["matrix"], method)
        reparsed = parse_newick(write_newick(t))
        a, b = ph.cophenetic(t), ph.cophenetic(reparsed)
        assert a["names"] == b["names"]
        for ra, rb in zip(a["matrix"], b["matrix"]):
            for xa, xb in zip(ra, rb):
                assert xa == pytest.approx(xb, abs=1e-6)
