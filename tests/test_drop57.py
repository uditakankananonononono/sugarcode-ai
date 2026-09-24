"""Drop 57: packaging pass - real CLI entry point, metadata, version 0.2.0."""
import json
import subprocess

import sugarcode
from sugarcode.cli import main


def test_version_alignment():
    assert sugarcode.__version__ == "0.2.0"
    pp = open("pyproject.toml").read()
    assert 'version = "0.2.0"' in pp
    assert 'sugarcode = "sugarcode.cli:main"' in pp
    assert 'readme = "README.md"' in pp


def test_cli_version_and_modules(capsys):
    assert main(["version"]) == 0
    assert "0.2.0" in capsys.readouterr().out
    assert main(["modules"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("89 modules")
    assert "deepsplice" in out


def test_cli_splice_assess_live(capsys):
    assert main(["splice", "assess", "RB1", "c.2490-28T>G"]) == 0
    d = json.loads(capsys.readouterr().out)
    assert d["status"] == "cryptic_scan"
    assert d["branchpoint"]["delta"] == -0.7937


def test_cli_splice_assess_unparseable(capsys):
    assert main(["splice", "assess", "BRCA1", "p.Arg273His"]) == 0
    d = json.loads(capsys.readouterr().out)
    assert d["status"] == "unparseable"
