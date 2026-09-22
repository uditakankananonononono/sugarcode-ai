"""Drop 59: repo hygiene - no generated build metadata in the source tree.

Locks the git-ops catch from drop 58: src/sugarcode_ai.egg-info/ was
committed by accident. .gitignore now covers egg-info/build/caches and a
test asserts none exist in the tree.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_gitignore_covers_build_artifacts():
    text = (ROOT / ".gitignore").read_text()
    for pattern in ("*.egg-info/", "build/", "__pycache__/", ".pytest_cache/"):
        assert pattern in text, pattern


def test_no_egg_info_or_build_dirs_in_tree():
    offenders = [
        p for p in ROOT.rglob("*")
        if p.is_dir() and (p.name.endswith(".egg-info") or p.name == "build")
    ]
    assert offenders == [], [str(p) for p in offenders]
