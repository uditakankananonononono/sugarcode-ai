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
    # Git-tracked files only: CI's `pip install -e .` legitimately regenerates
    # src/sugarcode_ai.egg-info/ in the working tree; the hygiene rule is that
    # no such artifact is COMMITTED, which is what drop 58 caught.
    import subprocess
    r = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                       text=True, check=True)
    tracked = r.stdout.split()
    offenders = [
        f for f in tracked
        if ".egg-info/" in f or f.endswith(".egg-info")
        or "/build/" in f or f.startswith("build/")
    ]
    assert offenders == [], offenders
