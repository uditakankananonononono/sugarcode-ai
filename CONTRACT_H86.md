# H86: literal nonnumeric BED score rejection

## Scope

Two additions only: `tests/test_h86_bed_nonnumeric_score_characterization.py`
and this contract. Product source and existing tests remain unchanged.

One literal `parse_bed("chr1\t0\t10\tx\tbad")` call pins exact exception
identity `ValueError` and exact text `line 1: score not numeric: 'bad'`.
Current float conversion raises ValueError, which the score handler replaces
with this diagnostic. Expected text comes from current source, not a numeric
oracle. No general numeric policy, coordinate semantics, BED conformance,
successful-parse, consumer, model, or biology claim.

## Documentary read gate

Base: `08fb03bd9a8345df47de1ba598301d7c272bc27c`.
2026-10-10 IST: parent ratified scope at 23:46:55. Fresh public HTTPS
fetch at 23:47:10 found 08fb03bd; full bed.py, test_bio_bed.py and
test_cli_bed.py visibly read before authoring. Existing bio_bed score
rejection uses NaNx and substring matching, not this exact diagnostic.
No exhaustive collision-search claim. Related prefix tests and relevant
CLI consumers were read for H82; no fresh consumer-read claim here.
Chronology is author self-report, not independent certification.

## Actual author receipts

Python 3.10.12, pytest 9.1.1, existing private environment.

- New file: 1 passed (`new.xml`).
- New + test_bio_bed.py + test_cli_bed.py: 16 passed (`adjacent.xml`).
- tests/self_improve + those same three files: 1856 passed, 13 xfailed
  (`wider.xml`). This is not the global suite.
- Restored-source adjacent selection: 16 passed (`restored.xml`).

Four independent temporary parse_bed mutants fail the new test with exit 1:

1. Remove score conversion handler: raw float ValueError text fails equality,
   `could not convert string to float: 'bad'`.
2. Return None from the handler: DID NOT RAISE ValueError.
3. Change diagnostic: exact text fails with `line 1: bad score: 'bad'`.
4. Change exception class to RuntimeError: exception escapes.

Each mutant started from original source; finally-block restoration,
cache removal and byte-exact source comparison were performed.
Restored bed.py SHA256:
`8f8a6cce995c76b9b16cf5d4df5ff661b96c4f0a1e6f9522627327bd8482e420`.
Receipt archive includes XMLs, mutant log and reproducer. Candidate/tree/
parent hashes and committed new-file blobs are in the manifest.
No mutation is committed. Separate audit and explicit publication handoff
are still required; no push is performed by this author.
