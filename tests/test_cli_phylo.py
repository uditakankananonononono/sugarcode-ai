"""CLI phylo subcommands (drop 68)."""
import json

from sugarcode.cli import main
from test_bio_newick import TREE


def _write(tmp_path):
    f = tmp_path / "tree.nwk"
    f.write_text(TREE)
    return str(f)


def test_cli_phylo_stats(capsys, tmp_path):
    assert main(["phylo", "stats", _write(tmp_path)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["leaves"] == 4 and out["height"] == 1.1 and out["binary"]


def test_cli_phylo_mrca(capsys, tmp_path):
    assert main(["phylo", "mrca", _write(tmp_path), "--leaves", "A,B"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["mrca"]["name"] == "AB" and out["mrca"]["subtree_nodes"] == 2


def test_cli_phylo_distance(capsys, tmp_path):
    assert main(["phylo", "distance", _write(tmp_path), "--a", "A",
                 "--b", "D"]) == 0
    assert json.loads(capsys.readouterr().out)["distance"] == 1.5


def test_cli_phylo_prune(capsys, tmp_path):
    assert main(["phylo", "prune", _write(tmp_path), "--drop", "B,D"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("(") and "B" not in out.replace("AB", "")
