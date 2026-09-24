"""SugarCode lab report & export engine (dependency-free).

HTML/Markdown report rendering with provenance blocks, CSV/TSV exporters,
executable Jupyter notebook generation and sha256-checksummed evidence
bundles. Pure stdlib; every renderer takes an optional deterministic
timestamp for reproducible output.
"""
from .engine import render_html_report, render_markdown_report
from .exporters import to_csv, to_tsv, make_bundle, write_bundle
from .notebook import new_notebook, validate_notebook, notebook_json

__all__ = [
    "render_html_report", "render_markdown_report",
    "to_csv", "to_tsv", "make_bundle", "write_bundle",
    "new_notebook", "validate_notebook", "notebook_json",
]
