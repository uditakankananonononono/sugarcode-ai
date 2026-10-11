"""Glow report renderer (v2 visual pass): typed-block HTML with a header
band, section cards, status pills, dark-mode/print CSS, responsive tables.

Same block contract and validation behavior as report.engine; HTML only.
"""
import pytest

from sugarcode.report.glow import STATUS_VOCAB, render_glow_report


def _sections():
    return [
        {"heading": "Summary", "blocks": [
            {"type": "paragraph", "text": "A paragraph."},
            {"type": "kv", "items": {"gene": "BRCA1", "classification": "pathogenic"}},
            {"type": "note", "text": "watch this"},
        ]},
        {"heading": "Data", "blocks": [
            {"type": "table", "columns": ["a", "b"], "rows": [[1, 2], [3, 4]]},
            {"type": "list", "items": ["one", "two"]},
            {"type": "provenance", "items": ["source: test", "limitation: none"]},
        ]},
    ]


# --- contract parity with report.engine ---------------------------------

def test_renders_all_block_types():
    out = render_glow_report("T", _sections(), generated_utc="2026-09-24T00:00:00+00:00")
    assert "<h1>T</h1>" in out and "Generated 2026-09-24" in out
    assert "<p>A paragraph.</p>" in out
    assert "<th>gene</th><td>BRCA1</td>" in out
    assert "class='note'" in out
    assert "<thead><tr><th>a</th><th>b</th></tr></thead>" in out
    assert "<li>one</li>" in out
    assert "Provenance &amp; limitations" in out


def test_escapes_everywhere():
    evil = "<script>alert(1)</script>"
    out = render_glow_report(evil, [{"heading": evil, "blocks": [
        {"type": "paragraph", "text": evil},
        {"type": "kv", "items": {evil: evil}},
        {"type": "table", "columns": [evil], "rows": [[evil]]},
        {"type": "list", "items": [evil]},
        {"type": "note", "text": evil},
        {"type": "provenance", "items": [evil]},
    ]}], footer=evil)
    assert "<script>" not in out
    assert out.count("&lt;script&gt;") >= 9


def test_title_and_section_validation():
    with pytest.raises(ValueError):
        render_glow_report("", _sections())
    with pytest.raises(ValueError):
        render_glow_report("T", [])
    with pytest.raises(TypeError):
        render_glow_report("T", ["not a dict"])
    with pytest.raises(ValueError):
        render_glow_report("T", [{"heading": "  ", "blocks": []}])
    with pytest.raises(ValueError):
        render_glow_report("T", [{"heading": "S", "blocks": "nope"}])
    with pytest.raises(ValueError) as ei:
        render_glow_report("T", [{"heading": "S", "blocks": [{"type": "weird"}]}])
    assert "unknown block type" in str(ei.value)


def test_deterministic_given_generated_utc():
    a = render_glow_report("T", _sections(), generated_utc="2026-01-01T00:00:00+00:00")
    b = render_glow_report("T", _sections(), generated_utc="2026-01-01T00:00:00+00:00")
    assert a == b


# --- F1 header band -------------------------------------------------------

def test_header_band_wraps_title_and_meta():
    out = render_glow_report("My Report", _sections(), generated_utc="2026-09-24T00:00:00+00:00")
    band = out.split("<header class='band'>", 1)[1].split("</header>", 1)[0]
    assert "<h1>My Report</h1>" in band
    assert "Generated 2026-09-24" in band
    assert ".band{" in out and "linear-gradient" in out


# --- F2 section cards -----------------------------------------------------

def test_each_section_is_a_card():
    out = render_glow_report("T", _sections())
    assert out.count("<section class='card'>") == 2
    assert "border-radius" in out and "box-shadow" in out


def test_card_contains_its_heading():
    out = render_glow_report("T", _sections())
    first_card = out.split("<section class='card'>", 1)[1].split("</section>", 1)[0]
    assert "<h2>Summary</h2>" in first_card


# --- F3 status pills ------------------------------------------------------

def test_known_status_value_becomes_pill():
    out = render_glow_report("T", _sections())
    assert "<span class='pill pill-bad'>pathogenic</span>" in out


@pytest.mark.parametrize("value,cls", [
    ("pathogenic", "pill-bad"), ("fail", "pill-bad"), ("high", "pill-bad"),
    ("likely pathogenic", "pill-warn"), ("vus", "pill-warn"), ("warn", "pill-warn"),
    ("benign", "pill-good"), ("pass", "pill-good"), ("ok", "pill-good"),
    ("likely benign", "pill-neutral"),
])
def test_status_vocab_classes(value, cls):
    out = render_glow_report("T", [{"heading": "S", "blocks": [
        {"type": "kv", "items": {"k": value}}]}])
    assert f"<span class='pill {cls}'>{value}</span>" in out
    assert STATUS_VOCAB[value] == cls


def test_status_match_is_case_insensitive():
    out = render_glow_report("T", [{"heading": "S", "blocks": [
        {"type": "kv", "items": {"k": "Pathogenic"}}]}])
    assert "<span class='pill pill-bad'>Pathogenic</span>" in out


def test_unknown_value_renders_plain():
    out = render_glow_report("T", [{"heading": "S", "blocks": [
        {"type": "kv", "items": {"k": "weird-status"}}]}])
    assert "pill" not in out.split("<tbody", 1)[1].split("</table>", 1)[0]
    assert "<td>weird-status</td>" in out


def test_nonstring_kv_values_render_plain():
    out = render_glow_report("T", [{"heading": "S", "blocks": [
        {"type": "kv", "items": {"delta": -0.25, "n": 3}}]}])
    assert "<td>-0.25</td>" in out and "<td>3</td>" in out
    assert "pill" not in out.split("<table", 1)[1].split("</table>", 1)[0]


def test_pill_like_injection_stays_escaped():
    out = render_glow_report("T", [{"heading": "S", "blocks": [
        {"type": "kv", "items": {"k": "pass<script>"}}]}])
    assert "<span class='pill" not in out
    assert "pass&lt;script&gt;" in out


# --- F4 dark mode + print --------------------------------------------------

def test_dark_mode_and_print_css_present():
    out = render_glow_report("T", _sections())
    assert "@media (prefers-color-scheme:dark)" in out
    assert "@media print" in out
    assert ":root{" in out and "--bg" in out and "--ink" in out


# --- F5 responsive tables ---------------------------------------------------

def test_tables_wrapped_for_horizontal_scroll():
    out = render_glow_report("T", _sections())
    assert "<div class='table-wrap'><table>" in out
    assert "overflow-x:auto" in out
    assert "nth-child(even)" in out


# --- module shape -----------------------------------------------------------

def test_module_is_stdlib_only():
    import ast, pathlib
    tree = ast.parse(pathlib.Path(
        __import__("sugarcode.report.glow", fromlist=["x"]).__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", None) or node.names[0].name.split(".")[0]
            assert mod.split(".")[0] in {"html", "datetime", "__future__"}, mod


def test_kv_tables_also_wrapped():
    out = render_glow_report("T", [{"heading": "S", "blocks": [
        {"type": "kv", "items": {"a": 1}}]}])
    assert out.count("<div class='table-wrap'><table>") == 1


def test_dark_mode_headings_keep_contrast():
    out = render_glow_report("T", _sections())
    dark = out.split("@media (prefers-color-scheme:dark)", 1)[1]
    # headings use var(--accent); the dark palette must brighten it
    assert "--accent:#52b788" in dark


def test_banner_renders_visibly_when_given():
    out = render_glow_report("T", _sections(), banner="SYNTHETIC DEMO DATA")
    assert "<div class='banner'>SYNTHETIC DEMO DATA</div>" in out
    assert ".banner{" in out


def test_banner_is_escaped():
    out = render_glow_report("T", _sections(), banner="<b>fake</b>")
    assert "<b>fake</b>" not in out and "&lt;b&gt;fake&lt;/b&gt;" in out


def test_no_banner_by_default():
    assert "class='banner'" not in render_glow_report("T", _sections())
