# H74: longer C row rejection

## Scope

Two additions only: `tests/test_h74_jaspar_row_lengths_characterization.py`
and this contract. Product source and existing tests remain unchanged.

One literal `read_jaspar(">toy\nA [ 1 ]\nC [ 1 2 ]\nG [ 1 ]\nT [ 1 ]\n")`
call pins exact exception type `ValueError` and exact text
`toy: rows have different lengths`. All four row keys exist; C has two
entries vs A's one. Current row-length guard rejects before PWM construction.
Expected text comes from current source, not a parser oracle. No all-input,
successful-parse, PWM, format-standard, accuracy, or biological claim.

## Documentary read gate

Base: `216bc1cc70e8451dc5ed77f2465fe0befcbbd4df`.
2026-10-10 IST: full motif.py, test_bio_motif.py and test_cli_motif.py
visibly read at 23:15:32, with relevant CLI loader/handlers and repository
coverage search. Existing unequal-length rejection uses A longer than the
other rows and matches a substring; no exact diagnostic pin was found.
No exhaustive coverage claim. Parent ratified at 23:16:05 and confirmed
at 23:16:16 that pytest.raises catches accepted returns as DID NOT RAISE,
with no successful-return assertion needed; five-mutant set confirmed.
Fresh public HTTPS fetch at 23:16:26 confirmed the same base and full
source/direct-test visible re-anchor preceded authoring. Chronology is an
author self-report, not independent certification.

## Actual author receipts

Python 3.10.12, pytest 9.1.1, existing private environment.

- New file: 1 passed (`new.xml`).
- New + test_bio_motif.py + test_cli_motif.py: 9 passed (`adjacent.xml`).
- tests/self_improve + those same three files: 1849 passed, 13 xfailed
  (`wider.xml`). This is not the global suite.
- Restored-source adjacent selection: 9 passed (`restored.xml`).

Five independent temporary finalizer mutants each fail the new test
with exit 1:

1. Remove length guard: DID NOT RAISE ValueError.
2. Replace any with all: DID NOT RAISE ValueError.
3. Replace != with <: DID NOT RAISE ValueError.
4. Change diagnostic: exact text assertion fails with `toy: unequal rows`.
5. Change exception class to RuntimeError: exception escapes.

Each mutant started from original source; finally-block restoration,
cache removal and byte-exact source comparison were performed.
Restored source SHA256:
`74252072c1cd38b37e4fb1b1b4d9b10de9d6e872722bce0359b1d98da57a6902`.
Receipt archive includes XMLs, mutant log and reproducer. Candidate/tree/
parent hashes and committed new-file blobs are in the manifest.
No mutation is committed. Separate audit and explicit publication handoff
are still required; no push is performed by this author.
