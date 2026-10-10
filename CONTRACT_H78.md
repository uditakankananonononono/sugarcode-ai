# H78: literal unequal-length build_pwm rejection

## Scope

Two additions only: `tests/test_h78_pwm_unequal_lengths_characterization.py`
and this contract. Product source and existing tests remain unchanged.

One literal `build_pwm(["A", "AC"])` call pins exact exception type
`ValueError` and exact text `sequences must be aligned to equal length`.
Nonempty guard passes; the second sequence length differs from the first
before the counts loop. Expected text comes from current source, not a
matrix oracle. No all-input/general alignment, matrix construction,
scoring, normalization, consumer, or biology claim.

## Documentary read gate

Base: `98f3f835b322fc60f60b0470ba9d92a8a72b25a9`.
2026-10-10 IST: full pwm.py, test_bio_utils.py, test_bio_motif.py and
P05 test visibly read at 23:28:07, with relevant motif wrapper/seed/CLI
consumer sections inspected and repository coverage search. Existing
wrapper ["ACG", "ACGT"] rejection matches a substring; H76 pins [] only.
No direct exact unequal-length diagnostic pin was found. No exhaustive
coverage claim. Parent had ruled P05's dropped list unit scoping, not a
standing ban, and ratified H78 at 23:28:34.
Fresh public HTTPS fetch at 23:28:47 confirmed the same base, and full
pwm.py and selected direct/adjacent test visible re-anchor preceded
writing the test. Chronology is author self-report, not certification.

## Actual author receipts

Python 3.10.12, pytest 9.1.1, existing private environment.

- New file: 1 passed (`new.xml`).
- New + test_bio_utils.py + test_bio_motif.py +
  test_p05_pwm_normalized_score_unknown_base.py: 18 passed (`adjacent.xml`).
- tests/self_improve + those same four files: 1858 passed, 13 xfailed
  (`wider.xml`). This is not the global suite.
- Restored-source adjacent selection: 18 passed (`restored.xml`).

Five independent temporary build_pwm mutants fail the new test with exit 1:

1. Remove length guard: DID NOT RAISE ValueError.
2. Replace any with all: DID NOT RAISE ValueError.
3. Replace != with <: DID NOT RAISE ValueError.
4. Change diagnostic: exact text fails with `unequal sequences`.
5. Change exception class to RuntimeError: exception escapes.

Each mutant started from original source; finally-block restoration,
cache removal and byte-exact source comparison were performed.
Restored pwm.py SHA256:
`5c227a131dbdbfcc6b95a66daa7aeb2327c3c1c7a268e8207b83b02a7c6d6b5c`.
Receipt archive includes XMLs, mutant log and reproducer. Candidate/tree/
parent hashes and committed new-file blobs are in the manifest.
No mutation is committed. Separate audit and explicit publication handoff
are still required; no push is performed by this author.
