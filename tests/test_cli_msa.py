"""CLI msa subcommands (drop 69)."""
import json

from sugarcode.cli import main
from test_bio_stockholm import STO, A3M


def test_cli_msa_stats_stockholm(capsys, tmp_path):
    f = tmp_path / "a.sto"; f.write_text(STO)
    assert main(["msa", "stats", str(f)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["nseq"] == 2 and out["width"] == 8


def test_cli_msa_stats_a3m_autodetect(capsys, tmp_path):
    f = tmp_path / "a.a3m"; f.write_text(A3M)
    assert main(["msa", "stats", str(f)]) == 0
    assert json.loads(capsys.readouterr().out)["width"] == 5


def test_cli_msa_consensus_and_pid(capsys, tmp_path):
    f = tmp_path / "a.sto"; f.write_text(STO)
    assert main(["msa", "consensus", str(f)]) == 0
    assert json.loads(capsys.readouterr().out)["consensus"] == "ACGTTGCA"
    assert main(["msa", "pid", str(f), "--a", "seq1", "--b", "seq2"]) == 0
    assert json.loads(capsys.readouterr().out)["identity"] == 1.0


def test_cli_msa_a2m_and_filter(capsys, tmp_path):
    f = tmp_path / "a.a3m"; f.write_text(A3M)
    assert main(["msa", "a2m", str(f)]) == 0
    out = capsys.readouterr().out
    assert ">master" in out and "ACGT-" in out and "de" not in out
    assert main(["msa", "filter", str(f), "--min-coverage", "0.5"]) == 0
    assert json is not None  # filter emits A3M text
