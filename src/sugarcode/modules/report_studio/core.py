"""Report Studio core: turn module outputs into lab-grade deliverables.

Every renderer is defensive about input shape (module outputs evolve),
never drops scalar data (unknown scalar fields land in a catch-all table),
and stamps provenance plus the platform disclaimer into every artifact.
"""
from __future__ import annotations

from ...report import (render_html_report, render_markdown_report,
                       to_csv, to_tsv, make_bundle,
                       new_notebook, validate_notebook, notebook_json)

DISCLAIMER = ("Computational research aid only - not clinical, diagnostic, "
              "or experimental evidence.")
_MAX_TABLE_ROWS = 50
_MAX_TABLE_COLS = 8
_MAX_SCALAR_LEN = 200


def _short(v) -> str:
    s = str(v)
    return s if len(s) <= _MAX_SCALAR_LEN else s[:_MAX_SCALAR_LEN] + "... [truncated]"


def _scalar_items(d: dict, skip: set[str]) -> dict[str, str]:
    items = {}
    for k, v in d.items():
        if k in skip:
            continue
        if isinstance(v, (str, int, float, bool)) or v is None:
            items[k] = _short(v)
    return items


def _tables(d: dict) -> list[tuple[str, list[str], list[list]]]:
    """Extract list-of-dict fields as (name, columns, rows) tables."""
    out = []
    for k, v in d.items():
        if not (isinstance(v, list) and v and all(isinstance(r, dict) for r in v)):
            continue
        cols: list[str] = []
        for r in v[:_MAX_TABLE_ROWS]:
            for ck, cv in r.items():
                if isinstance(cv, (str, int, float, bool)) or cv is None:
                    if ck not in cols:
                        cols.append(ck)
        cols = cols[:_MAX_TABLE_COLS]
        if not cols:
            continue
        rows = [[_short(r.get(c, "")) for c in cols] for r in v[:_MAX_TABLE_ROWS]]
        out.append((k, cols, rows))
    return out


def _finish(title: str, sections: list[dict], sources: list[str],
            generated_utc: str | None) -> dict:
    sections.append({"heading": "Provenance", "blocks": [
        {"type": "provenance",
         "items": sources + ["renderer: sugarcode report_studio", DISCLAIMER]}]})
    return {
        "title": title,
        "html": render_html_report(title, sections, generated_utc=generated_utc,
                                   footer=DISCLAIMER),
        "markdown": render_markdown_report(title, sections,
                                           generated_utc=generated_utc,
                                           footer=DISCLAIMER),
        "disclaimer": DISCLAIMER,
    }


def splice_assessment_report(assessment: dict, *,
                             generated_utc: str | None = None) -> dict:
    """Render a deepsplice live_splice_assessment-style dict as a
    clinician-readable HTML + Markdown report. Unknown scalar fields are
    preserved in a summary table; list-of-dict fields become data tables."""
    if not isinstance(assessment, dict) or not assessment:
        raise TypeError("assessment must be a non-empty dict")
    gene = assessment.get("gene", "")
    notation = assessment.get("notation", "")
    title = f"Splice assessment: {gene} {notation}".strip().rstrip(":") \
        if (gene or notation) else "Splice assessment report"
    blocks: list[dict] = []
    scalars = _scalar_items(assessment, skip=set())
    if scalars:
        blocks.append({"type": "kv", "items": scalars})
    tables = _tables(assessment)
    sections = [{"heading": "Assessment summary", "blocks": blocks or
                 [{"type": "paragraph", "text": "No scalar summary fields present."}]}]
    for name, cols, rows in tables:
        sections.append({"heading": f"Detail: {name} ({len(rows)} rows)",
                         "blocks": [{"type": "table", "columns": cols, "rows": rows}]})
    sources = ["source: deepsplice live_splice_assessment output dict"]
    if assessment.get("transcript"):
        sources.append(f"transcript: {assessment['transcript']}")
    return _finish(title, sections, sources, generated_utc)


def crispr_guides_report(guides: list[dict], *, target: str | None = None,
                         generated_utc: str | None = None) -> dict:
    """Render a ranked CRISPR guide set as HTML + Markdown with a guide table."""
    if not isinstance(guides, list) or not guides or \
            not all(isinstance(g, dict) for g in guides):
        raise TypeError("guides must be a non-empty list of dicts")
    title = f"CRISPR guide report: {target}" if target else "CRISPR guide report"
    preferred = ["sequence", "guide", "pam", "strand", "position",
                 "on_target", "off_target", "score", "cfd", "mit_score"]
    keys: list[str] = []
    for g in guides:
        keys.extend(k for k in g if k not in keys)
    cols = [k for k in preferred if k in keys] + \
           sorted(k for k in keys if k not in preferred)
    cols = cols[:_MAX_TABLE_COLS]
    rows = [[_short(g.get(c, "")) for c in cols] for g in guides[:_MAX_TABLE_ROWS]]
    summary = {"guide_count": len(guides)}
    if target:
        summary["target"] = target
    sections = [
        {"heading": "Summary", "blocks": [{"type": "kv", "items": summary}]},
        {"heading": f"Guides ({len(rows)})",
         "blocks": [{"type": "table", "columns": cols, "rows": rows}]},
    ]
    return _finish(title, sections,
                   ["source: caller-supplied guide set"], generated_utc)


def codon_optimization_report(result: dict, *,
                              generated_utc: str | None = None) -> dict:
    """Render a codon_opt optimize() result as HTML + Markdown."""
    if not isinstance(result, dict) or not result:
        raise TypeError("result must be a non-empty dict")
    blocks: list[dict] = []
    scalars = _scalar_items(result, skip={"dna", "sequence"})
    if scalars:
        blocks.append({"type": "kv", "items": scalars})
    dna = result.get("dna") or result.get("sequence")
    if isinstance(dna, str) and dna:
        blocks.append({"type": "paragraph",
                       "text": f"Optimized DNA ({len(dna)} nt): {dna}"})
    sections = [{"heading": "Optimization result", "blocks": blocks}]
    sections.extend(({"heading": f"Detail: {n} ({len(r)} rows)",
                      "blocks": [{"type": "table", "columns": c, "rows": r}]}
                     for n, c, r in _tables(result)))
    return _finish("Codon optimization report", sections,
                   ["source: codon_opt optimize() output dict"], generated_utc)


def csv_export(rows: list[dict], columns: list[str] | None = None) -> str:
    """CSV export of row dicts (see report.exporters.to_csv)."""
    return to_csv(rows, columns)


def tsv_export(rows: list[dict], columns: list[str] | None = None) -> str:
    """TSV export of row dicts."""
    return to_tsv(rows, columns)


def bundle_report(name: str, report: dict, *, metadata: dict | None = None,
                  created_utc: str | None = None) -> dict:
    """Package a report dict (html/markdown plus any csv/tsv strings keyed
    'csv'/'tsv') into a sha256-checksummed evidence bundle."""
    if not isinstance(report, dict):
        raise TypeError("report must be a dict of artifacts")
    artifacts = {}
    for key, fn in (("html", "report.html"), ("markdown", "report.md"),
                    ("csv", "report.csv"), ("tsv", "report.tsv")):
        if isinstance(report.get(key), str):
            artifacts[fn] = report[key]
    meta = dict(metadata or {})
    meta.setdefault("disclaimer", DISCLAIMER)
    if report.get("title"):
        meta.setdefault("title", report["title"])
    return make_bundle(name, artifacts, metadata=meta, created_utc=created_utc)


def splice_notebook(gene: str, notation: str, *, transcript: str | None = None,
                    offline: bool = False) -> dict:
    """Generate a real executable .ipynb reproducing a deepsplice assessment:
    install note, the exact live_splice_assessment call, and a JSON dump."""
    if not gene.strip() or not notation.strip():
        raise ValueError("gene and notation must be non-empty")
    args = f"{gene!r}, {notation!r}"
    kwargs = []
    if transcript:
        kwargs.append(f"transcript={transcript!r}")
    if offline:
        kwargs.append("offline=True")
    call = f"live_splice_assessment({args}{', ' if kwargs else ''}{', '.join(kwargs)})"
    cells = [
        {"cell_type": "markdown",
         "source": (f"# Splice assessment: {gene} {notation}\n\n"
                    f"Generated by sugarcode-ai report_studio. Requires "
                    f"`pip install sugarcode-ai` in this kernel.\n\n"
                    f"_{DISCLAIMER}_")},
        {"cell_type": "code",
         "source": ("from sugarcode.modules.deepsplice import live_splice_assessment\n"
                    f"assessment = {call}\n"
                    "assessment")},
        {"cell_type": "code",
         "source": ("import json\n"
                    "print(json.dumps(assessment, indent=1))")},
    ]
    nb = new_notebook(cells)
    problems = validate_notebook(nb)
    return {"notebook": nb, "json": notebook_json(nb),
            "valid": not problems, "problems": problems,
            "entrypoint": call}
