"""vina_real seed gate against the REAL RDKit / Vina / Open Babel stack. Skipped when any of them is missing."""
import importlib.util
import shutil
import subprocess
import sys

import pytest

HAVE = (importlib.util.find_spec("rdkit") is not None and importlib.util.find_spec("vina") is not None
        and shutil.which("obabel") is not None)
pytestmark = pytest.mark.skipif(not HAVE, reason="rdkit, vina and obabel are required")

DEEP = "import sys; sys.setrecursionlimit(10**7)\ns = []\nfor _ in range(100000): s = [s]\n"


def run(mod, call):
    body = DEEP + f"from sugarcode.modules.docking_studio import {mod} as m\nm.{call}\n"
    return subprocess.run([sys.executable, "-c", body], capture_output=True, text=True, timeout=120)


def test_unchecked_core_prepare_ligand_fails_on_nested_list_seed(tmp_path):
    r = run("vina_real", f"prepare_ligand_from_smiles('CCO', {str(tmp_path / 'a.pdbqt')!r}, seed=s)")
    assert r.returncode == 1 and r.stderr.strip().splitlines()[-1] != "" and "ArgumentError" in r.stderr
    assert not (tmp_path / "a.pdbqt").exists()


def test_unchecked_core_dock_fails_on_nested_list_seed():
    r = run("vina_real", "dock('/nonexistent/r.pdbqt', '/nonexistent/l.pdbqt', (0, 0, 0), seed=s)")
    assert r.returncode == 1 and "TypeError" in r.stderr and "new_Vina" in r.stderr


def test_checked_entries_refuse_nested_list_seed_before_any_work(tmp_path):
    r = run("seed_checked_vina", f"prepare_ligand_from_smiles('CCO', {str(tmp_path / 'b.pdbqt')!r}, seed=s)")
    assert r.returncode == 1 and r.stderr.strip().splitlines()[-1] == "TypeError: seed must be an integer"
    assert not (tmp_path / "b.pdbqt").exists()
    r = run("seed_checked_vina", "dock('/nonexistent/r.pdbqt', '/nonexistent/l.pdbqt', (0, 0, 0), seed=s)")
    assert r.returncode == 1 and r.stderr.strip().splitlines()[-1] == "TypeError: seed must be an integer"


def test_valid_seed_gives_identical_real_ligand_file(tmp_path):
    from sugarcode.modules.docking_studio import seed_checked_vina as sc, vina_real as core
    a, b = str(tmp_path / "core.pdbqt"), str(tmp_path / "wrap.pdbqt")
    assert core.prepare_ligand_from_smiles("CCO", a, seed=11) == a
    assert sc.prepare_ligand_from_smiles("CCO", b, seed=11) == b
    ta, tb = open(a).read(), open(b).read()
    assert "ATOM" in ta or "HETATM" in ta
    assert ta == tb
