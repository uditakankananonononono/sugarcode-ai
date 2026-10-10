# H67: whitespace-only consensus rejection

## Scope

Two additions only: `tests/test_h67_iupac_blank_consensus_characterization.py`
and this contract. Product source and existing tests remain unchanged.

One literal `from_iupac(" \t\n")` call pins exact exception type `ValueError`
and exact text `empty consensus`. The current upper().strip() makes this
literal empty before the empty-consensus guard. Expected text comes from
current source, not a construction oracle. No successful-construction,
PWM, standards, accuracy, or biological claim is made.

## Documentary read gate

Base: `ca9ec1154169be6441c5b68579a7c97ad6f43a4d`.
2026-10-10 IST: full motif.py, test_bio_motif.py and test_cli_motif.py
visibly read at 22:55:28, with relevant CLI loader/handlers and repository
coverage search. Existing from_iupac("") rejection matches substring
`empty`; no whitespace-only exact pin was found. No exhaustive coverage
claim. Parent ratified scope at 22:55:43 against then-tip 5734dcfe.
Fresh HTTPS public fetch at 22:55:54 found H65's two additions on ca9ec115;
fast-forward and full source/direct-test visible re-anchor preceded
private test authoring. Target files were unchanged. Parent confirmed
carrying unchanged scope on ca9ec115 at 22:56:50 before commit/package.
Chronology is an author self-report, not independent certification.

## Actual author receipts

Python 3.10.12, pytest 9.1.1, existing private environment.

- New file: 1 passed (`new.xml`).
- New + test_bio_motif.py + test_cli_motif.py: 9 passed (`adjacent.xml`).
- tests/self_improve + those same three files: 1849 passed, 13 xfailed
  (`wider.xml`). This is not the global suite.
- Restored-source adjacent selection: 9 passed (`restored.xml`).

Four independent temporary from_iupac mutants each fail the new test
with exit 1:

1. Omit strip: exact text assertion fails with `invalid IUPAC code ' '`.
2. Remove empty guard: no exception raised.
3. Change diagnostic to `blank consensus`: exact text assertion fails.
4. Change exception class to RuntimeError: exception escapes.

Each mutant started from original source; finally-block restoration,
cache removal and byte-exact source comparison were performed.
Restored source SHA256:
`74252072c1cd38b37e4fb1b1b4d9b10de9d6e872722bce0359b1d98da57a6902`.
Receipt archive includes XMLs, mutant log and reproducer. Candidate/tree/
parent hashes and committed new-file blobs are in the manifest.
No mutation is committed. Separate audit and explicit publication handoff
are still required.
