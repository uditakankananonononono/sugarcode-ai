"""CLI phylo dist/build/cophenetic subcommands (drop 78)."""
import json

import pytest

from sugarcode.cli import main
from sugarcode.bio.newick import parse_newick


def test_cli_phylo_dist(capsys, tmp_path):
    f = tmp_path / "aln.fa"
    f.write_text(">x\nAAAA\n>y\nAAAT\n")
    assert main(["phylo", "dist", "--fasta", str(f)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["names"] == ["x", "y"] and out["matrix"][0][1] == 0.25
    assert main(["phylo", "dist", "--fasta", str(f), "--model", "jc69"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["matrix"][0][1] == pytest.approx(0.3040988, abs=1e-6)


def test_cli_phylo_build(capsys, tmp_path):
    f = tmp_path / "aln.fa"
    f.write_text(">a\nACGTACGTAC\n>b\nACGTACGTAT\n>c\nACGAACGAAC\n")
    assert main(["phylo", "build", "--fasta", str(f), "--method", "upgma",
                 "--model", "pdistance"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["rooted"] is True
    from sugarcode.bio.newick import leaves
    t = parse_newick(out["newick"])
    assert sorted(leaves(t)) == ["a", "b", "c"]
    assert out["total_branch_length"] > 0
    assert main(["phylo", "build", "--fasta", str(f), "--method", "nj"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["rooted"] is False and parse_newick(out["newick"])


def test_cli_phylo_cophenetic(capsys, tmp_path):
    f = tmp_path / "t.nwk"
    f.write_text("(A:1,(B:2,C:3):4);\n")
    assert main(["phylo", "cophenetic", str(f)]) == 0
    out = json.loads(capsys.readouterr().out)
    i = {x: k for k, x in enumerate(out["names"])}
    assert out["matrix"][i["A"]][i["C"]] == 8.0
