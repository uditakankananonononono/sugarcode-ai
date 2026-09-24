"""CLI gff subcommands (drop 65)."""
import json

from sugarcode.cli import main
from test_bio_gff import GFF3


def _write(tmp_path):
    f = tmp_path / "anno.gff3"
    f.write_text(GFF3)
    return str(f)


def test_cli_gff_stats(capsys, tmp_path):
    assert main(["gff", "stats", _write(tmp_path)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["records"] == 6 and out["by_type"]["exon"] == 2
    assert out["format"] == "gff3"


def test_cli_gff_query(capsys, tmp_path):
    assert main(["gff", "query", _write(tmp_path), "--chrom", "chr1",
                 "--start", "180", "--end", "850"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["hits"] == 5
    assert out["records"][-1]["type"] == "CDS"


def test_cli_gff_filter_to_file(capsys, tmp_path):
    out_f = tmp_path / "genes.gff3"
    assert main(["gff", "filter", _write(tmp_path), "--type", "gene",
                 "--seqid", "chr1", "--out", str(out_f)]) == 0
    assert "5 of 6 records" in capsys.readouterr().out
    assert "##gff-version 3" in out_f.read_text()


def test_cli_gff_csv(capsys, tmp_path):
    assert main(["gff", "csv", _write(tmp_path)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert "attr_ID" in lines[0] and len(lines) == 7
