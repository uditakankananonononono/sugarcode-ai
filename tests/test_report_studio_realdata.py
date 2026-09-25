"""Module 118 report_studio: no silent truncation, no dropped scalar leaves, escaping."""
from sugarcode.modules.report_studio import (splice_assessment_report,
                                             crispr_guides_report, csv_export, tsv_export)


def test_truncation_is_stated_not_silent():
    big = {"verdict": "x", "effects": [{"site": str(i), "delta": i} for i in range(120)]}
    md = splice_assessment_report(big)["markdown"]
    assert "Detail: effects (120 rows, first 50 shown)" in md  # was "50 rows"
    g = [{"sequence": "G" * 20, "on_target": i / 100} for i in range(60)]
    assert "Guides (60, first 50 shown)" in crispr_guides_report(g)["markdown"]


def test_nested_scalar_leaves_are_never_dropped():
    a = {"gene": "RB1", "branchpoint": {"zone": "-45..-18", "drop_bits": 3.1747}}
    r = splice_assessment_report(a)
    assert "branchpoint.zone" in r["html"] and "3.1747" in r["html"]


def test_all_scalar_leaves_render_escaped():
    a = {"gene": "RB1", "notation": "c.2490-28T>G",
         "validation": "k>=3 golden: 0 FP", "delta": -0.7937,
         "nested": {"x": "<script>alert(1)</script>"}}
    r = splice_assessment_report(a)
    assert "c.2490-28T&gt;G" in r["html"] and "-0.7937" in r["html"]
    assert "<script>" not in r["html"] and "&lt;script&gt;" in r["html"]


def test_csv_tsv_quoting_roundtrip():
    rows = [{"a": 'x,"y"\nz', "b": "<b>&\t"}]
    import csv, io
    parsed = list(csv.DictReader(io.StringIO(csv_export(rows))))
    assert parsed[0]["a"] == 'x,"y"\nz'
    assert tsv_export(rows).splitlines()[0] == "a\tb"
