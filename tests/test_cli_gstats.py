"""CLI gstats subcommands (drop 81)."""
import json

import pytest

from sugarcode.cli import main


def test_cli_gstats_hwe(capsys):
    assert main(["gstats", "hwe", "--aa", "3", "--ab", "0", "--bb", "1"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["p_hwe_exact"] == pytest.approx(1 / 7)


def test_cli_gstats_allelic_and_genotypic(capsys):
    assert main(["gstats", "allelic", "--cases", "10,20,30",
                 "--controls", "30,20,10"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["table"] == [[40, 80], [80, 40]]
    assert main(["gstats", "genotypic", "--cases", "10,20,30",
                 "--controls", "30,20,10"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["statistic"] == pytest.approx(20.0)
    assert main(["gstats", "allelic", "--cases", "10,20,30",
                 "--controls", "30,20,10", "--yates"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["yates"] is True


def test_cli_gstats_or_and_adjust(capsys):
    assert main(["gstats", "or", "--a", "40", "--b", "60",
                 "--c", "50", "--d", "50"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["odds_ratio"] == pytest.approx(2 / 3)
    assert main(["gstats", "adjust", "--pvalues", "0.01,0.04,0.20",
                 "--method", "bonferroni"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["adjusted"] == pytest.approx([0.03, 0.12, 0.60])
    assert main(["gstats", "adjust", "--pvalues", "0.0001,0.3240,1.0"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["method"] == "bh"
    assert out["adjusted"] == pytest.approx([0.0003, 0.486, 1.0], abs=1e-9)
