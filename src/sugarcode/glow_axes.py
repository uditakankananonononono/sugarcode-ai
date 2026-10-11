"""C8 measured axes for the glow-up unit.

"x1,000,000" has no unit, so this module reports real before/after
measures instead: test counts (AST-parsed from real files), source module
count, and render latency measured with perf_counter over real renders.
Stdlib-only, deterministic counts; latency is a live measurement, never a
fixed constant.
"""
from __future__ import annotations

import ast
import statistics
import time
from pathlib import Path

MAX_REPEAT = 10_000


def count_test_files(root) -> int:
    """Number of test_*.py files under root (recursive)."""
    return sum(1 for _ in Path(root).rglob("test_*.py"))


def count_test_functions(root) -> int:
    """Number of top-level/inside-class functions named test_* across all
    test_*.py files, counted by AST (not string matching)."""
    total = 0
    for path in Path(root).rglob("test_*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                total += 1
    return total


def source_module_count(root) -> int:
    """Number of non-__init__ .py modules under root (recursive)."""
    return sum(1 for p in Path(root).rglob("*.py") if p.name != "__init__.py")


def axes_report(root, *, tests_dir: str = "tests", src_dir: str = "src") -> dict:
    """Static axes for one checkout: test files/functions and module count."""
    root = Path(root)
    tests_root = root / tests_dir
    src_root = root / src_dir
    return {
        "tests": {"files": count_test_files(tests_root), "functions": count_test_functions(tests_root)},
        "modules": source_module_count(src_root),
    }


def renderer_latency(render_fn, title: str, sections: list, *, repeat: int = 20) -> dict:
    """Measure render time over real renders. Returns milliseconds."""
    if not isinstance(repeat, int) or isinstance(repeat, bool) or not 1 <= repeat <= MAX_REPEAT:
        raise ValueError(f"repeat must be an integer in [1, {MAX_REPEAT}]")
    samples = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        render_fn(title, sections)
        samples.append((time.perf_counter() - t0) * 1000.0)
    return {"repeat": repeat, "min_ms": min(samples),
            "median_ms": statistics.median(samples), "max_ms": max(samples)}
