"""CLI motif subcommands (drop 74)."""
import json

from sugarcode.cli import main
from test_bio_motif import JASPAR


def test_cli_motif_scan_iupac(capsys):
    assert main(["motif", "scan", "--iupac", "WWWW", "--sequence",
                 "CCCCTTTTCCCC", "--fraction", "0.99"]) == 0
    out = json.loads(capsys.readouterr().out)
    hits = out["results"][0]["hits"]
    assert {h["strand"] for h in hits} == {"+", "-"}
    assert hits[0]["score"] == 4.0


def test_cli_motif_scan_jaspar_and_forward_only(capsys, tmp_path):
    f = tmp_path / "m.jaspar"; f.write_text(JASPAR)
    assert main(["motif", "scan", "--jaspar", str(f), "--sequence",
                 "GGGACGGG", "--forward-only", "--fraction", "0.99"]) == 0
    out = json.loads(capsys.readouterr().out)
    hits = out["results"][0]["hits"]
    assert len(hits) == 1 and hits[0]["matched"] == "ACG"


def test_cli_motif_info_and_convert(capsys, tmp_path):
    f = tmp_path / "sites.fa"; f.write_text(">s1\nACGT\n>s2\nACGT\n")
    assert main(["motif", "info", "--sites", str(f)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["length"] == 4 and out["consensus"] == "ACGT"
    assert out["max_score"] > 0 > out["min_score"]
    assert main(["motif", "to-jaspar", "--sites", str(f)]) == 0
    text = capsys.readouterr().out
    assert text.startswith(">") and "A  [" in text and "T  [" in text
