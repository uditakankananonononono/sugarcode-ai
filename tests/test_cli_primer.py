"""CLI primer subcommands (drop 73)."""
import json
import random

from sugarcode.cli import main


def test_cli_primer_tm(capsys):
    assert main(["primer", "tm", "CGTTCCAAAGATGTGGGCATGAGCTTAC"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["tm"] == 60.272 and out["gc_percent"] == 50.0


def test_cli_primer_check(capsys):
    assert main(["primer", "check", "GAATTC"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["self_dimer"] == {"any": 6, "three_prime": 6}
    assert "heuristic" in out["note"]


def test_cli_primer_pick(capsys, tmp_path):
    random.seed(42)
    template = "".join(random.choice("ACGT") for _ in range(600))
    f = tmp_path / "t.fa"
    f.write_text(f">t\n{template}\n")
    assert main(["primer", "pick", str(f), "--region", "250:350",
                 "--n", "2"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["region"] == [250, 350] and out["count"] == 2
    p = out["pairs"][0]
    assert p["product_size"] >= 100
    assert template[p["forward"]["start"]:p["forward"]["end"]] == \
        p["forward"]["seq"]
