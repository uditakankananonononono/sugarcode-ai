"""CLI align subcommands (drop 76)."""
import json

from sugarcode.cli import main


def test_cli_align_dna_global(capsys):
    assert main(["align", "run", "--a", "ACC", "--b", "A"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["mode"] == "global" and out["score"] == -4
    assert len(out["aligned_a"]) == len(out["aligned_b"])


def test_cli_align_local_and_blosum(capsys):
    assert main(["align", "run", "--a", "TTACGT", "--b", "GGACGGA",
                 "--mode", "local"]) == 0
    assert json.loads(capsys.readouterr().out)["score"] == 6
    assert main(["align", "run", "--a", "WWK", "--b", "WWK",
                 "--matrix", "BLOSUM62"]) == 0
    assert json.loads(capsys.readouterr().out)["score"] == 27


def test_cli_align_fasta(capsys, tmp_path):
    f = tmp_path / "pair.fa"; f.write_text(">x\nAA\n>y\nAA\n")
    assert main(["align", "run", "--fasta", str(f)]) == 0
    assert json.loads(capsys.readouterr().out)["score"] == 4
