"""CLI rnaseq subcommands (drop 80)."""
import json

import pytest

from sugarcode.cli import main


def _counts(tmp_path):
    f = tmp_path / "counts.tsv"
    f.write_text("gene\ts1\ts2\ts3\n"
                 "a\t10\t20\t40\nb\t5\t10\t20\nc\t1\t10\t100\n")
    return f


def test_cli_rnaseq_sizefactors_and_deseq(capsys, tmp_path):
    f = _counts(tmp_path)
    assert main(["rnaseq", "sizefactors", "--counts", str(f)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["size_factors"] == pytest.approx([0.5, 1.0, 2.0])
    assert main(["rnaseq", "normalize", "--counts", str(f),
                 "--method", "deseq"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["counts"][0] == pytest.approx([20.0, 20.0, 20.0])


def test_cli_rnaseq_cpm_and_out(capsys, tmp_path):
    f = _counts(tmp_path)
    o = tmp_path / "cpm.tsv"
    assert main(["rnaseq", "normalize", "--counts", str(f),
                 "--method", "cpm", "--out", str(o)]) == 0
    assert "wrote" in capsys.readouterr().out
    lines = o.read_text().splitlines()
    assert lines[0] == "gene\ts1\ts2\ts3"
    assert lines[1].split("\t")[1] == "625000"  # 10/16 * 1e6


def test_cli_rnaseq_tpm_and_filter(capsys, tmp_path):
    f = tmp_path / "c.tsv"
    f.write_text("gene\ts1\na\t10\nb\t30\n")
    L = tmp_path / "len.tsv"
    L.write_text("gene\tlength\na\t1000\nb\t3000\n")
    assert main(["rnaseq", "normalize", "--counts", str(f),
                 "--method", "tpm", "--lengths", str(L)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["counts"] == [[500000.0], [500000.0]]
    assert main(["rnaseq", "filter", "--counts", str(f),
                 "--min-count", "20"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["genes"] == ["b"]
