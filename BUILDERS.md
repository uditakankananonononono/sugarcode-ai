# BUILDERS.md - parallel-builder claims

One line per builder. Claim BEFORE starting work; do not edit another
builder's claimed files. Resolve collisions here, not in merge hell.

| Builder | Claim (files/dirs owned) | Scope | Started |
|---|---|---|---|
| lane-lead | provider-agnostic model layer (free local default; Fugu/Inkling optional endpoints) | per main-agent coordination 2026-09-24 | 2026-09-24 |
| pb3 | `src/sugarcode/report/`, `src/sugarcode/modules/report_studio/`, `tests/test_report_engine.py`, `tests/test_report_exporters.py`, `tests/test_report_notebook.py`, `tests/test_report_studio_spec.py`, `tests/test_cli_report.py`; additive-only edits: `src/omega/registry.py` (1 entry), `src/sugarcode/cli.py` (`report` subcommand), count bumps 88->89 in `tests/test_registry_health_search.py`, `tests/test_final_batch.py`, `tests/test_drop57.py`, `tests/test_drop60.py`, `tests/test_platform_modules.py`, `README.md`, `STATUS.md`, `src/omega/health.py` docstring | Lab Report & Export Engine: dependency-free HTML/Markdown lab reports with provenance blocks, CSV/TSV exporters, executable .ipynb (nbformat 4) generation, sha256-checksummed evidence bundles, CLI wiring, hermetic tests | 2026-09-24 |
