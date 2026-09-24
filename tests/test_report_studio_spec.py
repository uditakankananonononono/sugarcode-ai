"""Report Studio module: domain renderers on realistic module outputs."""
import json

import pytest

from sugarcode.modules.report_studio import (
    DISCLAIMER, splice_assessment_report, crispr_guides_report,
    codon_optimization_report, csv_export, bundle_report, splice_notebook)

ASSESSMENT = {
    "gene": "RB1", "notation": "c.2490-28T>G", "transcript": "NM_000321.2",
    "verdict": "strong loss", "delta": -0.7937,
    "branchpoint": {"zone": "-45..-18", "drop_bits": 3.1747},
    "effects": [
        {"site": "acceptor", "ref": 0.91, "alt": 0.12, "delta": -0.79},
        {"site": "cryptic", "ref": 0.0, "alt": 0.44, "delta": 0.44},
    ],
    "warnings": ["computational only"],
}


def test_splice_report_renders_scalars_and_tables():
    r = splice_assessment_report(ASSESSMENT,
                                 generated_utc="2026-09-24T00:00:00+00:00")
    assert r["title"] == "Splice assessment: RB1 c.2490-28T>G"
    assert "RB1" in r["html"] and "c.2490-28T&gt;G" in r["html"]
    assert "<th>delta</th><td>-0.7937</td>" in r["html"]
    assert "Detail: effects (2 rows)" in r["html"]
    assert "transcript: NM_000321.2" in r["html"]
    assert DISCLAIMER in r["html"] and DISCLAIMER in r["markdown"]
    assert "| site | ref | alt | delta |" in r["markdown"]


def test_splice_report_defensive_on_minimal_dict():
    r = splice_assessment_report({"verdict": "uncertain"})
    assert "uncertain" in r["html"] and r["title"] == "Splice assessment report"


def test_splice_report_rejects_non_dict():
    with pytest.raises(TypeError):
        splice_assessment_report([1, 2])


def test_crispr_report_prefers_known_columns():
    guides = [{"sequence": "GAGTCCGAGCAGAAGAAGAA", "zz_custom": 1,
               "on_target": 0.83, "off_target": 0.02},
              {"sequence": "CTGAAAAGGAACAAAGTCGG", "zz_custom": 2,
               "on_target": 0.71, "off_target": 0.05}]
    r = crispr_guides_report(guides, target="EMX1")
    head = r["markdown"].splitlines()
    table_head = [ln for ln in head if ln.startswith("| sequence")][0]
    assert "on_target" in table_head and "off_target" in table_head
    assert "guide_count**: 2" in r["markdown"]
    assert "EMX1" in r["title"]


def test_codon_report_includes_sequence_and_skips_blob_in_kv():
    r = codon_optimization_report({"protein_length": 5, "cai": 0.91,
                                   "dna": "ATGGCGGCGAAA", "gc": 0.75})
    assert "<th>cai</th><td>0.91</td>" in r["html"]
    assert "Optimized DNA (12 nt): ATGGCGGCGAAA" in r["html"]


def test_csv_export_passthrough():
    assert csv_export([{"a": 1}]).splitlines()[0] == "a"


def test_bundle_report_packages_artifacts():
    rep = splice_assessment_report(ASSESSMENT)
    rep["csv"] = csv_export(ASSESSMENT["effects"])
    b = bundle_report("rb1-evidence", rep, created_utc="2026-09-24T00:00:00+00:00")
    assert set(b["artifacts"]) == {"report.html", "report.md", "report.csv"}
    assert b["metadata"]["disclaimer"] == DISCLAIMER
    assert b["metadata"]["title"] == rep["title"]
    for a in b["artifacts"].values():
        assert len(a["sha256"]) == 64


def test_splice_notebook_is_valid_and_executable_shaped():
    r = splice_notebook("RB1", "c.2490-28T>G", transcript="NM_000321.2",
                        offline=True)
    assert r["valid"] and r["problems"] == []
    nb = json.loads(r["json"])
    code = nb["cells"][1]["source"]
    joined = "".join(code)
    assert "live_splice_assessment('RB1', 'c.2490-28T>G', transcript='NM_000321.2', offline=True)" in joined
    assert nb["cells"][0]["cell_type"] == "markdown"
    assert DISCLAIMER in "".join(nb["cells"][0]["source"])


def test_splice_notebook_requires_inputs():
    with pytest.raises(ValueError):
        splice_notebook("", "c.1A>G")
