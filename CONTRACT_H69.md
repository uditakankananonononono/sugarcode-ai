# H69: normalized invalid consensus code rejection

## Scope

Two additions only: `tests/test_h69_iupac_invalid_code_characterization.py`
and this contract. Product source and existing tests remain unchanged.

One literal `from_iupac("x")` call pins exact exception type `ValueError`
and exact text `invalid IUPAC code 'X'`. The current upper normalization
precedes the invalid-code guard. Expected text comes from current source,
not a construction oracle. No successful-construction, PWM, standards,
accuracy, or biological claim is made.

## Documentary read gate

Base: `a4f802f6090e20da4841dc7ddb8d38101974d47c`.
2026-10-10 IST: full motif.py, test_bio_motif.py and test_cli_motif.py
visibly read at 22:59:40, with relevant CLI loader/handlers and repository
coverage search. Existing from_iupac("AX") rejection matches substring
`IUPAC`; H67 pins the blank-consensus guard. No exact lowercase-invalid
code diagnostic pin was found. No exhaustive coverage claim.
Parent ratified scope at 22:59:50. Fresh public HTTPS fetch at 23:00:03
confirmed the same base, and full source/direct-test visible re-anchor
preceded authoring. Chronology is an author self-report, not independent
certification.

## Actual author receipts

Python 3.10.12, pytest 9.1.1, existing private environment.

- New file: 1 passed (`new.xml`).
- New + test_bio_motif.py + test_cli_motif.py: 9 passed (`adjacent.xml`).
- tests/self_improve + those same three files: 1849 passed, 13 xfailed
  (`wider.xml`). This is not the global suite.
- Restored-source adjacent selection: 9 passed (`restored.xml`).

Four independent temporary from_iupac mutants each fail the new test
with exit 1:

1. Omit upper normalization: text has lowercase 'x', fails equality.
2. Remove invalid-code guard: KeyError 'X' escapes.
3. Change diagnostic to `invalid code 'X'`: exact text assertion fails.
4. Change exception class to RuntimeError: exception escapes.

Each mutant started from original source; finally-block restoration,
cache removal and byte-exact source comparison were performed.
Restored source SHA256:
`74252072c1cd38b37e4fb1b1b4d9b10de9d6e872722bce0359b1d98da57a6902`.
Receipt archive includes XMLs, mutant log and reproducer. Candidate/tree/
parent hashes and committed new-file blobs are in the manifest.
No mutation is committed. Separate audit and explicit publication handoff
are still required.
