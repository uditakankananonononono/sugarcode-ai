"""CLI vcf subcommands (drop 63)."""
import json

from sugarcode.cli import main
from test_bio_vcf import MINI


def _write(tmp_path):
    f = tmp_path / "mini.vcf"
    f.write_text(MINI)
    return str(f)


def test_cli_vcf_stats(capsys, tmp_path):
    assert main(["vcf", "stats", _write(tmp_path)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["records"] == 5 and out["snps"]["ti_tv"] == 2.0
    assert out["by_type"]["snp"] == 3


def test_cli_vcf_filter_pass_only_to_file(capsys, tmp_path):
    out_f = tmp_path / "out.vcf"
    assert main(["vcf", "filter", _write(tmp_path), "--pass-only",
                 "--out", str(out_f)]) == 0
    assert "4 of 5 records" in capsys.readouterr().out
    assert out_f.read_text().count("\nchr1") == 4
    assert "##fileformat=VCFv4.2" in out_f.read_text()


def test_cli_vcf_filter_type_and_qual_stdout(capsys, tmp_path):
    assert main(["vcf", "filter", _write(tmp_path), "--type", "snp",
                 "--min-qual", "60"]) == 0
    out = capsys.readouterr().out
    assert out.count("\nchr1") == 2 and "rs1" not in out


def test_cli_vcf_csv_with_sample(capsys, tmp_path):
    assert main(["vcf", "csv", _write(tmp_path), "--sample", "S1"]) == 0
    lines = capsys.readouterr().out.splitlines()
    head = lines[0].split(",")
    assert "info_DP" in head and "fmt_GT" in head
    assert len(lines) == 6
