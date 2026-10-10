# H102: literal first blockStart incremental exact pin

## Scope and overlap

Exactly two additions: this contract and
`tests/test_h102_bed_first_blockstart_characterization.py`.
No product source or existing test changes.

One `parse_bed('chr1\t0\t9\tg\t0\t+\t0\t9\t0\t1\t8\t1')` call
pins exact ValueError identity and exact
`line 1: first blockStart must be 0` text. Count equals both list lengths
(1); first start 1 reaches this guard. Without guard, size 8 plus start 1
reaches end 9 and a record is returned. Existing ordinary direct regex
covers this same diagnostic on a different literal (interval 0..100,
size 10, start 5, trailing newline). H102 is incremental exact identity/
full-text on THIS literal only, no generic block or diagnostic novelty.
Source-derived diagnostic, no format/conformance, coordinate, consumer,
model, accuracy or biology claims; no other inputs or successful-parse pin.

## Documentary read gate

Base `5633f804a7d6096a1044790d41c8440bff83185c`.
2026-10-11 IST: parent ratified at 00:28:06; fresh public HTTPS fetch at
00:28:09 re-anchored onto 5633f804. Full bed.py, direct and CLI tests
visibly read before authoring. Existing regex overlap disclosed above.
No exhaustive collision-search claim. Chronology is author self-report,
not independent certification. Actual current source guard is lines 64/65
(parent proposal cited 63/64); literal semantics are unchanged.

## Actual receipts

Python 3.10.12, pytest 9.1.1, existing private environment.

- New: 1 passed, new.xml.
- New + bio_bed + cli_bed: 16 passed, adjacent.xml.
- tests/self_improve + same three files: 1856 passed, 13 xfailed,
  wider.xml. Selected suite, not global suite.
- Restored-source adjacent: 16 passed, restored.xml.

Four independent temporary mutants fail new-only with exit 1:

1. Return None: DID NOT RAISE ValueError.
2. Return text: DID NOT RAISE ValueError.
3. RuntimeError class: escapes.
4. Remove first-start guard: returns a record, DID NOT RAISE ValueError.

Each mutant starts from original bytes. Finally-block source restoration,
source cache removal and byte-exact comparison performed.
Restored bed.py SHA256:
`8f8a6cce995c76b9b16cf5d4df5ff661b96c4f0a1e6f9522627327bd8482e420`.
Archive includes XML/log/reproducer; manifest supplies candidate, tree,
parent and committed addition blobs. No mutations committed. Separate
audit/publication handoff required; no push by this author.
