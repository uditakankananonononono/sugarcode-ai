"""Drop 58: packaging pass 2 - clean-venv install, wheel data files, LICENSE.

Locks the packaging contract: the wheel must carry the bio data files
(codon tables, splice-site PWMs, branchpoint corpus) and a LICENSE file
must ship at the repo root. Root cause locked here: setuptools < 61
silently ignores [project] in pyproject.toml (UNKNOWN-0.0.0 wheel), and
pip 22.0.2 build isolation reproduces it even with a modern setuptools;
PEP 517 builds need setuptools >= 68 and a modern pip.
"""
import json
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "sugarcode" / "bio" / "data"


def test_license_file_present_and_proprietary():
    lic = ROOT / "LICENSE"
    assert lic.exists(), "LICENSE file missing at repo root"
    text = lic.read_text()
    assert "Proprietary" in text
    assert "Udita Phookan" in text
    assert "All rights reserved" in text


def test_pyproject_package_data_covers_bio_data():
    text = (ROOT / "pyproject.toml").read_text()
    assert "[tool.setuptools.package-data]" in text
    assert "sugarcode.bio" in text
    assert "data/" in text


def test_bio_data_files_exist_in_source_tree():
    assert (SRC / "codon_tables" / "e_coli_316407.csv").exists()
    assert (SRC / "codon_tables" / "h_sapiens_9606.csv").exists()
    for name in ("branchpoint_pwm.json", "acceptor_exon_pwm.json",
                 "acceptor_tract_pwm.json"):
        p = SRC / "splice_sites" / name
        assert p.exists(), name
        json.loads(p.read_text())
    assert (SRC / "codon_tables" / "PROVENANCE.md").exists()
    assert (SRC / "splice_sites" / "PROVENANCE.md").exists()
    for name in ("leman_rnaseq_bp.txt", "leman_variant_bp.txt"):
        assert (SRC / "branchpoints" / name).exists(), name


def test_wheel_contains_data_files_and_metadata(tmp_path):
    """Build a wheel in-process via PEP 517 and assert data + identity."""
    sbm = pytest.importorskip("setuptools.build_meta")
    import setuptools
    major = int(setuptools.__version__.split(".")[0])
    if major < 61:
        pytest.skip("setuptools < 61 ignores [project] (UNKNOWN-0.0.0 wheel)")
    whl_name = sbm.build_wheel(str(tmp_path))
    assert whl_name.startswith("sugarcode_ai-0.2.0"), whl_name
    names = zipfile.ZipFile(tmp_path / whl_name).namelist()
    assert any("codon_tables/e_coli_316407.csv" in n for n in names)
    assert any("splice_sites/branchpoint_pwm.json" in n for n in names)
    assert any("branchpoints/leman_rnaseq_bp.txt" in n for n in names)
    assert any(n.endswith(".dist-info/entry_points.txt") for n in names)
