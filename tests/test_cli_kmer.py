"""CLI kmer subcommands (drop 77)."""
import json

from sugarcode.cli import main


def test_cli_kmer_count_sequence(capsys):
    assert main(["kmer", "count", "--sequence", "AAAA", "--k", "2"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["distinct"] == 1 and out["total"] == 3
    assert out["top"] == [{"kmer": "AA", "count": 3}]


def test_cli_kmer_count_file(capsys, tmp_path):
    f = tmp_path / "x.fa"; f.write_text(">a\nAAAA\n>b\nCC\n")
    assert main(["kmer", "count", "--file", str(f), "--k", "2"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["distinct"] == 2 and out["total"] == 4


def test_cli_kmer_compare_exact(capsys):
    assert main(["kmer", "compare", "--a", "AAAA", "--b", "AAAT",
                 "--k", "2"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["mode"] == "exact" and out["jaccard"] == 0.5


def test_cli_kmer_compare_sketch(capsys):
    assert main(["kmer", "compare", "--a", "AAAA", "--b", "AAAT",
                 "--k", "2", "--w", "1"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["mode"] == "minimizer-sketch"
    assert out["jaccard_estimate"] == 0.5
    assert out["mash_distance"] > 0


def test_cli_kmer_sketch_lex(capsys):
    assert main(["kmer", "sketch", "--sequence", "TGCATGCA", "--k", "2",
                 "--w", "3", "--order", "lex",
                 "--no-canonical"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["minimizers"] == ["AT", "CA"]
    assert out["sketch_size"] == 2
