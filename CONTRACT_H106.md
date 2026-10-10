# H106: third-operand literal BED conversion pin

## Scope and overlap

Exactly two additions: this contract and
`tests/test_h106_bed_starts_conversion_characterization.py`.
No source or existing-test changes.

One `parse_bed('chr1\t0\t9\tg\t0\t+\t0\t9\t0\t1\t9\tx')` call
pins exact ValueError identity and `line 1: malformed block fields` text.
Count1 and size9 convert; starts-list x fails int at57, handler58/raise59.
H98 blockcount-x and H105 size-x pin the same handler/diagnostic on the
other operands. H106 is third-operand literal only, no generic diagnostic
novelty. Source-derived diagnostic, not external format oracle. No other
inputs, successful parsing, broad validation, format/conformance, coordinate,
consumer, model, accuracy or biology claims.

## Documentary read gate

Base `341097f4401eb09d58e4d5d570d24894a3a4c05b`.
2026-10-11 IST: parent ratified at 00:39:00; fresh public HTTPS fetch at
00:39:03 re-anchored onto 341097f4. Full bed.py, direct/CLI tests and
H98/H105 contracts visibly read before authoring. Overlap disclosed above.
No exhaustive collision-search claim. Chronology is author self-report,
not independent certification.

## Actual receipts

Python 3.10.12, pytest 9.1.1, existing private environment.

- New: 1 passed, new.xml.
- New + bio_bed + cli_bed: 16 passed, adjacent.xml.
- tests/self_improve + same three files: 1856 passed, 13 xfailed,
  wider.xml. Selected suite, not global suite.
- Restored-source adjacent: 16 passed, restored.xml.

Four independent temporary mutants fail new-only with exit 1:

1. Return None: DID NOT RAISE ValueError.
2. Return full text: DID NOT RAISE ValueError.
3. RuntimeError class: escapes.
4. Remove try/except wrapper, retain conversion statements: raw int
   ValueError identity passes but diagnostic equality fails.

Each mutant starts from original bytes. Finally-block source restoration,
source cache removal and byte-exact comparison performed.
Restored bed.py SHA256:
`8f8a6cce995c76b9b16cf5d4df5ff661b96c4f0a1e6f9522627327bd8482e420`.
Archive includes XML/log/reproducer; manifest supplies candidate, tree,
parent and committed addition blobs. No mutations committed. Separate
audit/publication handoff required; no push by this author.
