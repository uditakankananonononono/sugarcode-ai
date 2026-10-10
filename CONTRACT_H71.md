# H71: row before header after a blank line

## Scope

Two additions only: `tests/test_h71_jaspar_before_header_characterization.py`
and this contract. Product source and existing tests remain unchanged.

One literal `read_jaspar("\nA [ nope ]\n")` call pins exact exception type
`ValueError` and exact text `line 2: matrix row before any header`.
The current loop counts the blank line; the before-header guard rejects
before nonnumeric token parsing. Expected text comes from current source,
not a parser oracle. No all-input, successful-parse, format-standard,
accuracy, or biological claim is made.

## Documentary read gate

Base: `4a1bfbc4e963662fc073561eb3c2398ba891d152`.
2026-10-10 IST: full motif.py, test_bio_motif.py and test_cli_motif.py
visibly read at 23:04:45, with relevant CLI loader/handlers and repository
coverage search. Existing line-1 before-header rejection matches a
substring; H52 pins nonnumeric after header, H60 prefix after header,
and H64 blank-only. No exact line-2 before-header pin was found. No
exhaustive coverage claim. Parent ratified authoring/package at 23:05:20.
Fresh public HTTPS fetch at 23:05:32 confirmed the same base, and full
source/direct-test visible re-anchor preceded authoring. Chronology is an
author self-report, not independent certification.

## Actual author receipts

Python 3.10.12, pytest 9.1.1, existing private environment.

- New file: 1 passed (`new.xml`).
- New + test_bio_motif.py + test_cli_motif.py: 9 passed (`adjacent.xml`).
- tests/self_improve + those same three files: 1849 passed, 13 xfailed
  (`wider.xml`). This is not the global suite.
- Restored-source adjacent selection: 9 passed (`restored.xml`).

Four independent temporary read_jaspar mutants each fail the new test
with exit 1:

1. Enumerate start=0: text reports line 1, fails equality.
2. Remove before-header guard: text is `line 2: non-numeric count`.
3. Change diagnostic: text is `line 2: missing header`.
4. Change exception class to RuntimeError: exception escapes.

Each mutant started from original source; finally-block restoration,
cache removal and byte-exact source comparison were performed.
Restored source SHA256:
`74252072c1cd38b37e4fb1b1b4d9b10de9d6e872722bce0359b1d98da57a6902`.
Receipt archive includes XMLs, mutant log and reproducer. Candidate/tree/
parent hashes and committed new-file blobs are in the manifest.
No mutation is committed. Separate audit and explicit publication handoff
are still required; no push is performed by this author.
