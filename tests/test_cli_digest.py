"""CLI digest subcommands (drop 75)."""
import json

from sugarcode.cli import main


def test_cli_digest_run_sequence(capsys):
    assert main(["digest", "run", "--sequence", "TTTGAATTCAAA",
                 "--enzymes", "EcoRI", "--cuts"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["fragments"] == [8, 4]
    assert out["cuts"][0]["overhang"] == "5'"
    assert len(out["gel"]) == 2


def test_cli_digest_lambda_fasta(capsys):
    assert main(["digest", "run", "--fasta",
                 "tests/data/lambda_NC_001416.fasta",
                 "--enzymes", "HindIII,EcoRI"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["length"] == 48502 and sum(out["fragments"]) == 48502
    # EcoRI cuts the 23130 HindIII band into 21226 + 1904
    assert out["fragments"][0] == 21226 and 1904 in out["fragments"]


def test_cli_digest_list_and_info(capsys):
    assert main(["digest", "list", "--match", "eco"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert "EcoRI" in out["enzymes"]
    assert main(["digest", "info", "EcoRI"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["site"] == "GAATTC" and out["overhang"] == "5'"
