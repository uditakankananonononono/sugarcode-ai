"""CLI fastq subcommands (drop 64)."""
import json

from sugarcode.cli import main
from test_bio_fastq import READS


def _write(tmp_path):
    f = tmp_path / "reads.fq"
    f.write_text(READS)
    return str(f)


def test_cli_fastq_stats(capsys, tmp_path):
    assert main(["fastq", "stats", _write(tmp_path)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["reads"] == 3 and out["mean_phred"] == 25.73
    assert out["offset"] == 33


def test_cli_fastq_filter_to_file(capsys, tmp_path):
    out_f = tmp_path / "clean.fq"
    assert main(["fastq", "filter", _write(tmp_path), "--min-mean-phred", "20",
                 "--out", str(out_f)]) == 0
    assert "2 of 3 reads" in capsys.readouterr().out
    assert out_f.read_text().count("@r") == 2


def test_cli_fastq_trim_stdout(capsys, tmp_path):
    assert main(["fastq", "trim", _write(tmp_path), "--min-len", "3"]) == 0
    out = capsys.readouterr().out
    assert "@r2 low tail\nACG\n+\nIII\n" in out


def test_cli_fastq_to_fasta(capsys, tmp_path):
    assert main(["fastq", "to-fasta", _write(tmp_path)]) == 0
    assert capsys.readouterr().out.startswith(">r1 good read\n")
