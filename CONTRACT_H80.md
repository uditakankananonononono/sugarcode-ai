# H80: literal score length rejection

## Scope

Two additions only: `tests/test_h80_pwm_score_length_characterization.py`
and this contract. Product source and existing tests remain unchanged.

One literal `score("A", [])` call pins exact exception type `ValueError`
and exact text `sequence length must equal PWM length`. The sequence is
longer than the matrix; current guard rejects before sum. Expected text
comes from current source, not a scoring oracle. No successful score,
general bounds, matrix, normalization, consumer, or biology claim.

## Documentary read gate

Base: `0037ca58dfa14f7ca0c8b10728589dc0bb0d446c`.
2026-10-10 IST: full pwm.py, test_bio_utils.py, test_bio_motif.py and
P05 test visibly read at 23:31:52. Relevant score_site wrapper and CLI
PWM handler inspected; full drop60 CLI tests read at 23:31:58. Repository
coverage search found no direct exact mismatch pin. P05 is a separate
unknown-base normalized-score pin. No exhaustive coverage claim.
Parent ratified at 23:32:04 and permitted re-anchor to whatever public
tip was current at authoring. Fresh HTTPS fetch at 23:32:17 still found
0037ca58, with H79 not yet in public tip; full pwm.py and selected
direct/adjacent test visible re-anchor preceded writing the test.
Chronology is author self-report, not certification.

## Actual author receipts

Python 3.10.12, pytest 9.1.1, existing private environment.

- New file: 1 passed (`new.xml`).
- New + test_bio_utils.py + test_bio_motif.py +
  test_p05_pwm_normalized_score_unknown_base.py: 18 passed (`adjacent.xml`).
- tests/self_improve + those same four files: 1858 passed, 13 xfailed
  (`wider.xml`). This is not the global suite.
- Restored-source adjacent selection: 18 passed (`restored.xml`).

Five independent temporary score mutants fail the new test with exit 1:

1. Remove length guard: DID NOT RAISE ValueError.
2. Replace != with <: DID NOT RAISE ValueError.
3. Return 0 instead of raise: DID NOT RAISE ValueError.
4. Change diagnostic: exact text fails with `wrong length`.
5. Change exception class to RuntimeError: exception escapes.

Each mutant started from original source; finally-block restoration,
cache removal and byte-exact source comparison were performed.
Restored pwm.py SHA256:
`5c227a131dbdbfcc6b95a66daa7aeb2327c3c1c7a268e8207b83b02a7c6d6b5c`.
Receipt archive includes XMLs, mutant log and reproducer. Candidate/tree/
parent hashes and committed new-file blobs are in the manifest.
No mutation is committed. Separate audit and explicit publication handoff
are still required; no push is performed by this author.
