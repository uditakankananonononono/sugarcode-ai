"""Audit pins for the glow renderer (review round at c534e5a).

Covers: list-block ul placement outside the provenance div, well-formed
balanced tags, footer output, generated_utc escaping and type, head
metadata, table-wrap structure, full status vocabulary case-insensitively,
exact exception types, quote-escaping, and the demo doc banner.
"""
from html.parser import HTMLParser
from pathlib import Path

import pytest

from sugarcode.report.glow import STATUS_VOCAB, render_glow_report


def _sections():
    return [
        {"heading": "Data", "blocks": [
            {"type": "table", "columns": ["tool", "flag"], "rows": [["SpliceAI", "high"]]},
            {"type": "list", "items": ["donor gain: none"]},
            {"type": "provenance", "items": ["source: fixture"]},
        ]},
    ]


# --- 1. list-block ul sits outside the provenance div ---------------------

def test_list_ul_outside_provenance_div():
    out = render_glow_report("T", _sections())
    list_ul = out.index("<ul><li>donor gain: none</li></ul>")
    prov_open = out.index("<div class='provenance'>")
    prov_close = out.index("</div>", prov_open)
    assert list_ul < prov_open                      # list ul before provenance div
    assert "<ul><li>source: fixture</li></ul>" in out[prov_open:prov_close]  # provenance ul inside


# --- 2. well-formed balanced section/main/div tags ------------------------

class _Balance(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in ("meta", "br", "img", "hr", "link", "input"):
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"mismatch </{tag}> vs {self.stack[-3:]}")
        else:
            self.stack.pop()


def test_document_is_well_formed():
    out = render_glow_report("T", _sections(), footer="f", banner="B")
    p = _Balance()
    p.feed(out)
    assert p.errors == [] and p.stack == []
    assert out.count("<section") == out.count("</section>") == 1
    assert out.count("<main>") == out.count("</main>") == 1


# --- 3. footer text output -------------------------------------------------

def test_footer_text_is_output():
    out = render_glow_report("T", _sections(), footer="Generated for review <b>now</b>")
    assert "<footer class='meta'>Generated for review &lt;b&gt;now&lt;/b&gt;</footer>" in out


# --- 4. generated_utc escaped + typed --------------------------------------

def test_generated_utc_is_html_escaped():
    out = render_glow_report("T", _sections(), generated_utc="<script>x</script>")
    assert "<script>x</script>" not in out
    assert "Generated &lt;script&gt;x&lt;/script&gt;" in out


def test_generated_utc_non_str_is_typeerror():
    with pytest.raises(TypeError):
        render_glow_report("T", _sections(), generated_utc=123)


# --- 5. head metadata + title escaping --------------------------------------

def test_head_metadata_and_title_escaping():
    out = render_glow_report("He said \"hi\" <b>", _sections())
    assert "<meta charset='utf-8'>" in out
    assert "width=device-width,initial-scale=1" in out
    assert "<html lang='en'>" in out
    assert "<title>He said &quot;hi&quot; &lt;b&gt;</title>" in out


# --- 6. table wrap open/close, responsive ----------------------------------

def test_table_wrap_open_close_and_responsive():
    out = render_glow_report("T", _sections())
    assert out.count("<div class='table-wrap'>") == out.count("</table></div>") >= 1
    assert ".table-wrap{overflow-x:auto" in out


# --- 7. full status vocabulary, case-insensitive ----------------------------

@pytest.mark.parametrize("word", ["moderate", "benign", "low", "likely benign"])
def test_status_vocabulary_entries_exist(word):
    assert word in STATUS_VOCAB


@pytest.mark.parametrize("raw,cls", [
    ("Moderate", "pill-warn"), ("BENIGN", "pill-good"),
    ("Low", "pill-good"), ("Likely Benign", "pill-neutral"),
])
def test_status_vocabulary_case_insensitive(raw, cls):
    out = render_glow_report("T", [{"heading": "S", "blocks": [
        {"type": "kv", "items": {"k": raw}}]}])
    assert f"<span class='pill {cls}'>{raw}</span>" in out


# --- 8. exact exception types ------------------------------------------------

def test_non_str_title_is_valueerror():
    # parity with report.engine: wrong-type title is a ValueError there
    with pytest.raises(ValueError):
        render_glow_report(5, _sections())


def test_blank_title_is_valueerror():
    with pytest.raises(ValueError):
        render_glow_report("   ", _sections())


def test_non_list_sections_is_valueerror():
    # parity with report.engine: non-list sections is a ValueError there
    with pytest.raises(ValueError, match="sections must be a non-empty list"):
        render_glow_report("T", "not a list")


def test_non_str_heading_is_valueerror():
    # parity with report.engine: wrong-type heading is a ValueError there
    with pytest.raises(ValueError):
        render_glow_report("T", [{"heading": 7, "blocks": []}])


def test_blank_heading_is_valueerror():
    with pytest.raises(ValueError):
        render_glow_report("T", [{"heading": "", "blocks": []}])


# --- 9. quote escaping (kills the quote=False mutant) ------------------------

def test_double_quotes_are_escaped():
    out = render_glow_report('a "quoted" title', _sections())
    assert "a &quot;quoted&quot; title" in out


# --- banner present in the checked-in demo doc -------------------------------

def test_demo_doc_carries_synthetic_banner():
    doc = Path(__file__).resolve().parent.parent / "docs" / "demo_glow.html"
    assert "SYNTHETIC DEMO DATA" in doc.read_text(encoding="utf-8")


# --- S1. every STATUS_VOCAB key maps to its pill class -----------------------
# The expected mapping is a FIXED literal table here, never derived from
# STATUS_VOCAB itself - a table built from the module would adapt to a
# mutated vocabulary and let removals or remaps survive.

EXPECTED_STATUS_VOCAB = {
    "pathogenic": "pill-bad", "fail": "pill-bad", "error": "pill-bad", "high": "pill-bad",
    "likely pathogenic": "pill-warn", "vus": "pill-warn", "warn": "pill-warn",
    "moderate": "pill-warn",
    "benign": "pill-good", "pass": "pill-good", "ok": "pill-good", "low": "pill-good",
    "likely benign": "pill-neutral",
}


def test_status_vocab_matches_fixed_table():
    assert STATUS_VOCAB == EXPECTED_STATUS_VOCAB


@pytest.mark.parametrize("word,cls", sorted(EXPECTED_STATUS_VOCAB.items()))
def test_every_status_vocab_key_maps_to_its_pill(word, cls):
    out = render_glow_report("T", [{"heading": "S", "blocks": [
        {"type": "kv", "items": {"k": word}}]}])
    assert f"<span class='pill {cls}'>{word}</span>" in out


# --- S2. blank banner refuses -------------------------------------------------

def test_empty_banner_is_valueerror():
    with pytest.raises(ValueError, match="banner"):
        render_glow_report("T", _sections(), banner="")


def test_whitespace_banner_is_valueerror():
    with pytest.raises(ValueError, match="banner"):
        render_glow_report("T", _sections(), banner="   \t ")


def test_non_str_banner_is_valueerror():
    # pins the isinstance guard: dropping it yields an incidental
    # AttributeError from int.strip(), not a ValueError
    with pytest.raises(ValueError, match="banner"):
        render_glow_report("T", _sections(), banner=5)
