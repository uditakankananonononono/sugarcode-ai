"""CLI orf subcommands (drop 79)."""
import json

from sugarcode.cli import main


def test_cli_orf_translate(capsys):
    assert main(["orf", "translate", "ATGAAATAA"]) == 0
    assert json.loads(capsys.readouterr().out)["protein"] == "MK*"
    assert main(["orf", "translate", "TGATAA", "--table", "2"]) == 0
    assert json.loads(capsys.readouterr().out)["protein"] == "W*"


def test_cli_orf_find_sequence(capsys):
    assert main(["orf", "find", "--sequence", "CCATGAAAGGCTAACC",
                 "--min-aa", "1"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["count"] == 1
    o = out["orfs"][0]
    assert o["record"] is None and o["protein"] == "MKG"
    assert (o["start"], o["end"]) == (2, 14)


def test_cli_orf_find_fasta_and_alt_starts(capsys, tmp_path):
    f = tmp_path / "x.fa"
    f.write_text(">a\nGTGAAATAA\n>b\nATGAAATAA\n")
    assert main(["orf", "find", "--fasta", str(f), "--table", "11",
                 "--starts", "table", "--min-aa", "1"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["count"] == 2
    assert {o["record"] for o in out["orfs"]} == {"a", "b"}
    assert all(o["protein"] == "MK" for o in out["orfs"])
