"""Report engine: typed-block rendering, escaping, validation."""
import pytest

from sugarcode.report import render_html_report, render_markdown_report


def _sections():
    return [
        {"heading": "Summary", "blocks": [
            {"type": "paragraph", "text": "A paragraph."},
            {"type": "kv", "items": {"gene": "BRCA1", "delta": -0.25}},
            {"type": "note", "text": "watch this"},
        ]},
        {"heading": "Data", "blocks": [
            {"type": "table", "columns": ["a", "b"], "rows": [[1, 2], [3, 4]]},
            {"type": "list", "items": ["one", "two"]},
            {"type": "provenance", "items": ["source: test", "limitation: none"]},
        ]},
    ]


def test_html_renders_all_block_types():
    out = render_html_report("T", _sections(), generated_utc="2026-09-24T00:00:00+00:00")
    assert "<h1>T</h1>" in out and "Generated 2026-09-24" in out
    assert "<p>A paragraph.</p>" in out
    assert "<th>gene</th><td>BRCA1</td>" in out
    assert "class='note'" in out
    assert "<thead><tr><th>a</th><th>b</th></tr></thead>" in out
    assert "<li>one</li>" in out
    assert "Provenance &amp; limitations" in out


def test_html_escapes_data_text():
    evil = "<script>alert(1)</script>"
    out = render_html_report(evil, [{"heading": "S", "blocks": [
        {"type": "paragraph", "text": evil}]}])
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_unknown_block_type_raises():
    with pytest.raises(ValueError, match="unknown block type"):
        render_html_report("T", [{"heading": "S", "blocks": [{"type": "raw_html"}]}])


def test_section_validation():
    with pytest.raises(ValueError):
        render_html_report("T", [])
    with pytest.raises(ValueError):
        render_html_report("T", [{"heading": "  ", "blocks": []}])
    with pytest.raises(ValueError):
        render_html_report("  ", [{"heading": "S", "blocks": []}])


def test_markdown_renders_tables_and_provenance():
    out = render_markdown_report("T", _sections(),
                                 generated_utc="2026-09-24T00:00:00+00:00")
    assert out.startswith("# T")
    assert "## Data" in out
    assert "| a | b |" in out and "| 1 | 2 |" in out
    assert "- **gene**: BRCA1" in out
    assert "> watch this" in out
    assert "**Provenance & limitations**" in out
