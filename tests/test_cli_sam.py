"""CLI sam subcommands (drop 67)."""
import json

from sugarcode.cli import main
from test_bio_sam import SAM


def _write(tmp_path):
    f = tmp_path / "aln.sam"
    f.write_text(SAM)
    return str(f)


def test_cli_sam_stats(capsys, tmp_path):
    assert main(["sam", "stats", _write(tmp_path)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["reads"] == 4 and out["mapped_rate"] == 0.75
    assert out["mapq"]["mean"] == 31.67


def test_cli_sam_filter_to_file(capsys, tmp_path):
    out_f = tmp_path / "f.sam"
    assert main(["sam", "filter", _write(tmp_path), "--mapped-only",
                 "--primary-only", "--out", str(out_f)]) == 0
    assert "2 of 4 alignments" in capsys.readouterr().out
    assert out_f.read_text().startswith("@HD")


def test_cli_sam_to_bed(capsys, tmp_path):
    assert main(["sam", "to-bed", _write(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "chr1\t99\t109\tr001\t60\t+" in out
    assert "NNNN" not in out
