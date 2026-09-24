"""CLI protein props (drop 72)."""
import json

from sugarcode.cli import main
from test_bio_proteinprops import INSULIN_B


def test_cli_protein_props_sequence(capsys):
    assert main(["protein", "props", "--sequence", INSULIN_B]) == 0
    out = json.loads(capsys.readouterr().out)
    p = out["proteins"][0]
    assert p["id"] == "cli" and p["length"] == 30
    assert 6.5 < p["isoelectric_point"] < 7.5


def test_cli_protein_props_fasta(capsys, tmp_path):
    f = tmp_path / "p.fa"
    f.write_text(f">insB\n{INSULIN_B}\n>aa\nAA\n")
    assert main(["protein", "props", str(f)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert [p["id"] for p in out["proteins"]] == ["insB", "aa"]
    assert out["proteins"][1]["molecular_weight"] == 160.17
