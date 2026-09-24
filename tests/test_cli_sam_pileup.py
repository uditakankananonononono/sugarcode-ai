"""CLI sam pileup (drop 70)."""
import json

from sugarcode.cli import main
from test_bio_pileup import SAM


def _write(tmp_path):
    f = tmp_path / "aln.sam"
    f.write_text(SAM)
    return str(f)


def test_cli_sam_pileup_json(capsys, tmp_path):
    assert main(["sam", "pileup", _write(tmp_path)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert len(out["positions"]) == 7
    p3 = [p for p in out["positions"] if p["pos"] == 3][0]
    assert p3["counts"] == {"G": 1, "T": 1, "g": 1}
    assert p3["insertions"] == {"+1A": 1}
    assert any(s["pos"] == 2 for s in out["variant_sites"])


def test_cli_sam_pileup_mpileup_format(capsys, tmp_path):
    assert main(["sam", "pileup", _write(tmp_path), "--format", "mpileup",
                 "--min-mapq", "25"]) == 0
    out = capsys.readouterr().out
    lines = out.rstrip("\n").split("\n")
    assert lines[0].split("\t")[:3] == ["chr1", "1", "N"]
    assert "*\t" not in out                              # r3 filtered out
