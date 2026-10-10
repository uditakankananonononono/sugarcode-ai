# H76: literal empty-list build_pwm rejection

## Scope

Two additions only: `tests/test_h76_pwm_empty_sequences_characterization.py`
and this contract. Product source and existing tests remain unchanged.

One literal `build_pwm([])` call pins exact exception type `ValueError`
and exact text `no sequences`. Current guard rejects before aligned_seqs[0]
access. Expected text comes from current source, not a matrix oracle.
No aligned-length, general empty-like/falsy, matrix construction, valid
parsing, standard, normalization, scoring, consumer, or biology claim.

## Documentary read gate

Base: `6d370cf0153c1f5a57294cf7794cd2516b231572`.
2026-10-10 IST: full pwm.py and direct test_bio_utils.py read at
23:20:13-18. An oversized related read was repeated in smaller visible
reads at 23:20:20-33: full drop28/drop44/P05/bio_motif tests and motif.py;
relevant seed/CLI consumer sections inspected. Coverage search found
nonempty build_pwm calls and a separate unequal-length wrapper substring
case, no direct empty-list exact pin. No exhaustive coverage claim.
P05's dropped-edge list was read; parent ruled at 23:20:40 it was unit
scoping, not a standing ban. Parent ratified H76 at 23:21:01.
Fresh public HTTPS fetch at 23:21:14 confirmed the same base, and full
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

Four independent temporary build_pwm mutants fail the new test with exit 1:

1. Remove empty guard: IndexError escapes.
2. Return [] instead of raising: DID NOT RAISE ValueError.
3. Change diagnostic: exact text fails with `empty sequences`.
4. Change exception class to RuntimeError: exception escapes.

Each mutant started from original source; finally-block restoration,
cache removal and byte-exact source comparison were performed.
Restored pwm.py SHA256:
`5c227a131dbdbfcc6b95a66daa7aeb2327c3c1c7a268e8207b83b02a7c6d6b5c`.
Receipt archive includes XMLs, mutant log and reproducer. Candidate/tree/
parent hashes and committed new-file blobs are in the manifest.
No mutation is committed. Separate audit and explicit publication handoff
are still required; no push is performed by this author.
