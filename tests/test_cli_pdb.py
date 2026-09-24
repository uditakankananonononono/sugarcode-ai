"""CLI pdb subcommands (drop 71)."""
import json

from sugarcode.cli import main
from test_bio_pdb import PDB, MMCIF


def test_cli_pdb_stats(capsys, tmp_path):
    f = tmp_path / "t.pdb"; f.write_text(PDB)
    assert main(["pdb", "stats", str(f)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["atoms"] == 6 and out["chains"] == ["A", "B"]
    assert out["hetatms"] == 1


def test_cli_mmcif_autodetect(capsys, tmp_path):
    f = tmp_path / "t.cif"; f.write_text(MMCIF)
    assert main(["pdb", "stats", str(f)]) == 0
    assert json.loads(capsys.readouterr().out)["format"] == "mmcif"


def test_cli_pdb_contacts(capsys, tmp_path):
    f = tmp_path / "t.pdb"; f.write_text(PDB)
    assert main(["pdb", "contacts", str(f), "--cutoff", "2.0",
                 "--chain-a", "A", "--chain-b", "B"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert len(out["contacts"]) == 2
    assert out["contacts"][1]["distance"] == 0.3317


def test_cli_pdb_select_and_chains(capsys, tmp_path):
    f = tmp_path / "t.pdb"; f.write_text(PDB)
    assert main(["pdb", "select", str(f), "--record", "HETATM"]) == 0
    out = capsys.readouterr().out
    assert "HETATM" in out and "ATOM  " not in out and "O1" in out
    assert main(["pdb", "chains", str(f), "--residues", "--chain", "A"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["chains"] == ["A", "B"] and len(out["residues"]) == 2
