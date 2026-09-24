"""Newick toolkit: parse, roundtrip, traversals, MRCA, distance, prune."""
import pytest

from sugarcode.bio.newick import (parse_newick, write_newick, leaves, stats,
                                  mrca, distance, prune)

TREE = "((A:0.1,B:0.2)AB:0.3,(C:0.4,D:0.5)CD:0.6)R;\n"


def test_parse_nested_with_lengths():
    t = parse_newick(TREE)
    assert t["name"] == "R" and t["length"] is None
    ab, cd = t["children"]
    assert ab["name"] == "AB" and ab["length"] == 0.3
    assert [c["name"] for c in ab["children"]] == ["A", "B"]
    assert cd["children"][1]["length"] == 0.5


def test_roundtrip_exact():
    assert write_newick(parse_newick(TREE)) == TREE


def test_quoted_names_and_comments():
    t = parse_newick("('it''s A':1,'B x':2)[&rooted]R;\n")
    assert leaves(t) == ["it's A", "B x"]
    out = write_newick(t)
    assert "'it''s A'" in out and "'B x'" in out


def test_stats_shape_and_math():
    s = stats(parse_newick(TREE))
    assert s["nodes"] == 7 and s["leaves"] == 4 and s["internal_nodes"] == 3
    assert s["binary"] is True
    assert s["total_branch_length"] == 2.1
    assert s["height"] == 1.1
    assert s["edges_missing_length"] == 0
    assert s["leaf_names"] == ["A", "B", "C", "D"]


def test_polytomy_not_binary():
    t = parse_newick("(A:1,B:1,C:1)R;")
    assert stats(t)["binary"] is False


def test_mrca_deepest_common():
    t = parse_newick(TREE)
    assert mrca(t, ["A", "B"])["name"] == "AB"
    assert mrca(t, ["A", "C"])["name"] == "R"
    assert mrca(t, ["A", "B", "C", "D"])["name"] == "R"
    assert mrca(t, ["B"])["name"] == "B"
    with pytest.raises(ValueError, match="unknown leaves"):
        mrca(t, ["A", "ZZ"])


def test_distance_through_mrca():
    t = parse_newick(TREE)
    assert distance(t, "A", "B") == 0.3
    assert distance(t, "A", "D") == round(0.1 + 0.3 + 0.6 + 0.5, 6)
    assert distance(t, "A", "A") == 0.0
    with pytest.raises(ValueError, match="unknown leaf"):
        distance(t, "A", "ZZ")


def test_prune_collapses_lone_children():
    t = parse_newick(TREE)
    p = prune(t, ["B", "D"])
    assert leaves(p) == ["A", "C"]
    assert distance(p, "A", "C") == 1.4          # lengths merged, not lost
    p2 = prune(t, ["A", "B"])
    assert leaves(p2) == ["C", "D"]
    with pytest.raises(ValueError, match="unknown leaves"):
        prune(t, ["ZZ"])
    with pytest.raises(ValueError, match="every leaf"):
        prune(t, ["A", "B", "C", "D"])


def test_malformed_inputs_raise():
    with pytest.raises(ValueError, match="end with ';'"):
        parse_newick("(A,B)R")
    with pytest.raises(ValueError, match="expected '\\)'"):
        parse_newick("(A,B;")
    with pytest.raises(ValueError, match="invalid branch length"):
        parse_newick("(A:x,B:1)R;")
    with pytest.raises(ValueError, match="unterminated"):
        parse_newick("('A:1,B:2)R;")
    with pytest.raises(ValueError, match="trailing content"):
        parse_newick("(A,B)R; extra")
