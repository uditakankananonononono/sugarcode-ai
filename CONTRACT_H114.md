# H114: literal negative-size BED pin

## Scope and overlap

Exactly two additions: this contract and
`tests/test_h114_bed_negative_size_characterization.py`.
No source or existing-test changes.

One `parse_bed('chr1\t0\t9\tg\t0\t+\t0\t9\t0\t1\t-1\t0')` call
pins exact ValueError type and full text
`line 1: block at +0 size -1 escapes the interval`.
Count1 matches, first start0; only b<1 rejects, not overshoot.
H103 size0 uses same b<1 clause; H104 positive overshoot uses different
clause. Ordinary direct regex covers positive overshoot on another literal.
H114 is negative-size literal only, not generic diagnostic or validation
novelty. Source-derived diagnostic, no external format/coordinate oracle.
No other inputs, successful parsing, broad policy, format/conformance,
consumer, model, accuracy or biology claims.

## Documentary read gate

Base `05fc2a6040ad8a49b13077a613d1e468592ec8f9`.
2026-10-11 IST: parent ratified at 00:48:38; public HTTPS fetch at 00:48:41
re-anchored onto fresh actual tip 05fc2a60. Full bed.py, direct/CLI tests and
H103/H104 contracts visibly read before authoring. Overlap disclosed above.
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
4. Remove only b<1 clause, retain overshoot: accepts record,
   DID NOT RAISE ValueError.

Each mutant starts from original bytes. Finally-block source restoration,
source cache removal and byte-exact comparison performed.
Restored bed.py SHA256:
`8f8a6cce995c76b9b16cf5d4df5ff661b96c4f0a1e6f9522627327bd8482e420`.
Archive includes XML/log/reproducer; manifest supplies candidate, tree,
parent and committed addition blobs. No mutations committed. Separate
audit/publication handoff required; no push by this author.
