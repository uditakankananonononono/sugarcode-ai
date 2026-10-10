# H66: negative threshold fraction rejection

## Scope

Two additions only: `tests/test_h66_motif_negative_fraction_characterization.py`
and this contract. Product source and existing tests remain unchanged.

One literal `threshold_score({"min_score": 0, "max_score": 1}, -0.1)` call
pins exact exception type `ValueError` and exact text
`fraction must be in [0, 1]`. The lower-bound side of the current chained
comparison fails before score arithmetic. Expected text comes from current
source, not a scoring oracle. No successful-score, accuracy, format-standard,
or biological claim is made.

## Documentary read gate

Base: `5976b7ae6da57c89115b75a590f611acc3c937fd`.
2026-10-10 IST: full motif.py, test_bio_motif.py and test_cli_motif.py
visibly read at 22:51:44; CLI motif loader and handlers and repository
coverage search read in the same call. The existing fraction=1.1 rejection
uses substring matching and covers the upper-bound side; no exact
negative-fraction pin was found. No exhaustive coverage claim.
Parent ratified at 22:51:53. Fresh public HTTPS fetch, unchanged base and
full source/direct-test visible re-anchor at 22:52:06 preceded authoring.
This chronology is an author self-report, not independent certification.

## Actual author receipts

Python 3.10.12, pytest 9.1.1, existing private environment.

- New file: 1 passed (`new.xml`).
- New + test_bio_motif.py + test_cli_motif.py: 9 passed (`adjacent.xml`).
- tests/self_improve + those same three files: 1849 passed, 13 xfailed
  (`wider.xml`). This is not the global suite.
- Restored-source adjacent selection: 9 passed (`restored.xml`).

Four independent temporary threshold_score mutants each fail the new test
with exit 1: omit lower bound and relax it to -1.0 both raise no exception;
change diagnostic to `bad fraction` fails equality; change exception class
to RuntimeError escapes the expected exception context.

Each mutant started from original source; finally-block restoration,
cache removal and byte-exact source comparison were performed.
Restored source SHA256:
`74252072c1cd38b37e4fb1b1b4d9b10de9d6e872722bce0359b1d98da57a6902`.
Receipt archive includes XMLs, mutant log and reproducer. Candidate/tree/
parent hashes and committed new-file blobs are in the manifest.
No mutation is committed. Separate audit and explicit publication handoff
are still required.
