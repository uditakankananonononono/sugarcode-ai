# H72: header-only row-set rejection

## Scope

Two additions only: `tests/test_h72_jaspar_header_only_characterization.py`
and this contract. Product source and existing tests remain unchanged.

One literal `read_jaspar(">toy\n")` call pins exact exception type
`ValueError` and exact text `toy: need exactly 4 rows A/C/G/T, got []`.
The current EOF finalizer runs with header `toy` and empty rows; the
row-set guard rejects before rows["A"] access. Expected text comes from
current source, not a parser oracle. No all-input, successful-parse,
format-standard, accuracy, or biological claim is made.

## Documentary read gate

Base: `67983407137a0a46b9813379792b4f76b27cf3b5`.
2026-10-10 IST: full motif.py, test_bio_motif.py and test_cli_motif.py
visibly read at 23:10:09, with relevant CLI loader/handlers and repository
coverage search. Existing missing-T rejection matches a substring;
no header-only exact diagnostic pin was found. No exhaustive coverage
claim. Parent ratified authoring/package at 23:10:40. The ratification
rendered the leading > as an HTML entity but referred to the unchanged
read-only proposal's header-only literal. The test uses that proposed >.
Fresh public HTTPS fetch at 23:10:53 confirmed the same base, and full
source/direct-test visible re-anchor preceded authoring. Chronology is an
author self-report, not independent certification.

## Actual author receipts

Python 3.10.12, pytest 9.1.1, existing private environment.

- New file: 1 passed (`new.xml`).
- New + test_bio_motif.py + test_cli_motif.py: 9 passed (`adjacent.xml`).
- tests/self_improve + those same three files: 1849 passed, 13 xfailed
  (`wider.xml`). This is not the global suite.
- Restored-source adjacent selection: 9 passed (`restored.xml`).

Four independent temporary mutants each fail the new test with exit 1:

1. Remove EOF finalizer: text is `no JASPAR matrices found`.
2. Remove row-set guard: KeyError 'A' escapes.
3. Change diagnostic: text is `toy: missing rows, got []`.
4. Change exception class to RuntimeError: exception escapes.

Each mutant started from original source; finally-block restoration,
cache removal and byte-exact source comparison were performed.
Restored source SHA256:
`74252072c1cd38b37e4fb1b1b4d9b10de9d6e872722bce0359b1d98da57a6902`.
Receipt archive includes XMLs, mutant log and reproducer. Candidate/tree/
parent hashes and committed new-file blobs are in the manifest.
No mutation is committed. Separate audit and explicit publication handoff
are still required; no push is performed by this author.
