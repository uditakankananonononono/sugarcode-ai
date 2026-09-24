"""CLI de subcommands (drop 82)."""
import json

import pytest

from sugarcode.cli import main


def _counts(tmp_path):
    f = tmp_path / "counts.tsv"
    f.write_text("gene\ts1\ts2\ts3\ts4\n"
                 "g1\t10\t12\t40\t44\n"
                 "g2\t20\t22\t21\t19\n"
                 "g3\t5\t7\t6\t8\n")
    return f


def test_cli_de_run(capsys, tmp_path):
    f = _counts(tmp_path)
    assert main(["de", "run", "--counts", str(f),
                 "--groups", "A,A,B,B"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["method"] == "welch" and out["n_a"] == 2
    assert "not a negative-binomial model" in out["scope"]
    g1 = out["results"][0]
    assert g1["gene"] == "g1" and g1["log2fc"] > 1.5
    assert g1["padj"] >= g1["pvalue"]


def test_cli_de_run_wilcoxon_and_out(capsys, tmp_path):
    f = _counts(tmp_path)
    o = tmp_path / "de.tsv"
    assert main(["de", "run", "--counts", str(f), "--groups", "A,A,B,B",
                 "--method", "wilcoxon", "--out", str(o)]) == 0
    assert "wrote" in capsys.readouterr().out
    lines = o.read_text().splitlines()
    assert lines[0] == "gene\tmean_a\tmean_b\tlog2fc\tstatistic\tpvalue\tpadj"
    assert len(lines) == 4  # header + 3 genes
