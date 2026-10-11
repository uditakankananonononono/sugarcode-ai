"""C8 measured axes: test count, module count, render latency, and a
before/after report over the repo. 'x1,000,000' has no unit; these axes
report real before/after measures instead. All counts come from AST
parsing of real files; latency is perf_counter over real renders.
"""
import json

import pytest

from sugarcode.glow_axes import (axes_report, renderer_latency, source_module_count,
                                 count_test_files, count_test_functions)
from sugarcode.report.engine import render_html_report
from sugarcode.report.glow import render_glow_report

REPO = __import__("pathlib").Path(__file__).resolve().parent.parent


def test_test_counts_on_fixture(tmp_path):
    (tmp_path / "test_a.py").write_text("def test_one():\n    pass\n\ndef test_two():\n    pass\n")
    (tmp_path / "test_b.py").write_text("def helper():\n    pass\n\ndef test_three():\n    pass\n")
    (tmp_path / "not_a_test.py").write_text("def test_hidden():\n    pass\n")
    assert count_test_files(tmp_path) == 2
    assert count_test_functions(tmp_path) == 3


def test_module_count_excludes_init(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "a.py").write_text("X = 1\n")
    sub = pkg / "sub"
    sub.mkdir()
    (sub / "__init__.py").write_text("")
    (sub / "b.py").write_text("Y = 2\n")
    assert source_module_count(tmp_path) == 2


def test_axes_report_shape_and_json(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text("def test_one():\n    pass\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "m.py").write_text("X = 1\n")
    r = axes_report(tmp_path, tests_dir="tests", src_dir="src")
    assert r["tests"] == {"files": 1, "functions": 1}
    assert r["modules"] == 1
    json.dumps(r, sort_keys=True)  # must be JSON-serializable


# Floors over the live repo, recomputed every run - deliberately NOT exact
# counts, so the suite does not pin fixed repo output. Synthetic fixtures
# above keep exact counts because their inputs are fixed by the test.
FLOOR_TEST_FILES = 400
FLOOR_TEST_FUNCTIONS = 1000
FLOOR_MODULES = 100


def test_repo_axes_sanity():
    r = axes_report(REPO)
    assert r["tests"]["files"] > FLOOR_TEST_FILES
    assert r["tests"]["functions"] > FLOOR_TEST_FUNCTIONS
    assert r["modules"] > FLOOR_MODULES


def _sections():
    return [{"heading": "S", "blocks": [
        {"type": "paragraph", "text": "x"},
        {"type": "table", "columns": ["a"], "rows": [[1], [2]]}]}]


def test_renderer_latency_measures_real_renders():
    for fn in (render_html_report, render_glow_report):
        m = renderer_latency(fn, "T", _sections(), repeat=5)
        assert m["repeat"] == 5 and set(m) == {"repeat", "min_ms", "median_ms", "max_ms"}
        assert 0 <= m["min_ms"] <= m["median_ms"] <= m["max_ms"]
        assert m["max_ms"] < 1000  # sanity: a small report renders in far less than a second


def test_latency_repeat_validated():
    with pytest.raises(ValueError):
        renderer_latency(render_glow_report, "T", _sections(), repeat=0)
    with pytest.raises(ValueError):
        renderer_latency(render_glow_report, "T", _sections(), repeat=10_001)


def test_glow_vs_engine_latency_comparable():
    e = renderer_latency(render_html_report, "T", _sections(), repeat=20)
    g = renderer_latency(render_glow_report, "T", _sections(), repeat=20)
    # glow does strictly more work but must stay within 50x of the engine
    assert g["median_ms"] <= 50 * max(e["median_ms"], 1e-9)


def test_module_is_stdlib_only():
    import ast, pathlib
    tree = ast.parse(pathlib.Path(
        __import__("sugarcode.glow_axes", fromlist=["x"]).__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", None) or node.names[0].name.split(".")[0]
            assert mod.split(".")[0] in {"ast", "pathlib", "statistics", "time", "__future__"}, mod
