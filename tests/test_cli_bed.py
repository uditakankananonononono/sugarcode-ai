"""CLI bed subcommands (drop 66)."""
import json

from sugarcode.cli import main
from test_bio_bed import BED


def _write(tmp_path):
    f = tmp_path / "iv.bed"
    f.write_text(BED)
    return str(f)


def test_cli_bed_stats(capsys, tmp_path):
    assert main(["bed", "stats", _write(tmp_path)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["records"] == 4 and out["bases_covered"] == 270


def test_cli_bed_merge(capsys, tmp_path):
    assert main(["bed", "merge", _write(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "chr1\t0\t200\n" in out and out.count("\nchr") == 2


def test_cli_bed_merge_strict(capsys, tmp_path):
    assert main(["bed", "merge", _write(tmp_path), "-d", "-1"]) == 0
    out = capsys.readouterr().out
    assert "chr1\t0\t150\n" in out and out.count("\nchr") == 3


def test_cli_bed_filter_to_file(capsys, tmp_path):
    out_f = tmp_path / "f.bed"
    assert main(["bed", "filter", _write(tmp_path), "--min-width", "60",
                 "--out", str(out_f)]) == 0
    assert "2 of 4 records" in capsys.readouterr().out
    assert out_f.read_text().startswith("track name=demo")


def test_cli_bed_to_gff(capsys, tmp_path):
    assert main(["bed", "to-gff", _write(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "##gff-version 3" in out
    assert "chr1\tbed\tregion\t1\t100\t50\t+\t.\tName=first" in out
