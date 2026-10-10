# H104: incremental literal positive-overshoot pin

## Scope and overlap

Exactly two additions: this contract and
`tests/test_h104_bed_positive_overshoot_characterization.py`.
Product source and old tests unchanged.

One `parse_bed('chr1\t0\t9\tg\t0\t+\t0\t9\t0\t1\t10\t0')` call
pins exact ValueError identity and full text
`line 1: block at +0 size 10 escapes the interval`. Count matches 1,
first start 0, size 10 positive; only overshoot clause rejects (0+0+10>9).
Ordinary direct regex already tests positive overshoot on a different
literal (end100, two blocks, second size95 at+10). H103 exact pin is size0.
H104 is incremental exact identity/full-text on THIS literal only, no
generic validation novelty. Source-derived diagnostic, not independent
coordinate oracle. No other inputs, successful parsing, format/conformance,
consumer, model, accuracy or biology claims.

## Documentary read gate

Base `3f95dd5bfd0b332157699a75a0afdb33ef7db6ef`.
2026-10-11 IST: parent ratified at 00:33:19; fresh public HTTPS fetch at
00:33:23 re-anchored onto 3f95dd5f. Full bed.py, direct/CLI tests and
H103 contract visibly read before authoring. Existing regex and H103 overlap
disclosed above. No exhaustive collision-search claim. Read chronology is
author self-report, not independent certification.

## Actual receipts

Python 3.10.12, pytest 9.1.1, existing private environment.

- New: 1 passed, new.xml.
- New + bio_bed + cli_bed: 16 passed, adjacent.xml.
- tests/self_improve + same three files: 1856 passed, 13 xfailed,
  wider.xml. Selected suite, not global suite.
- Restored-source adjacent: 16 passed, restored.xml.

Four independent temporary mutants fail new-only with exit 1:

1. Return None at guard: DID NOT RAISE ValueError.
2. Return full text at guard: DID NOT RAISE ValueError.
3. RuntimeError class: escapes.
4. Remove only overshoot clause, retain b<1: returns record,
   DID NOT RAISE ValueError.

Each mutant starts from original bytes. Finally-block source restoration,
source cache removal and byte-exact comparison performed.
Restored bed.py SHA256:
`8f8a6cce995c76b9b16cf5d4df5ff661b96c4f0a1e6f9522627327bd8482e420`.
Archive includes XML/log/reproducer; manifest supplies candidate, tree,
parent and committed addition blobs. No mutations committed. Separate
audit/publication handoff required; no push by this author.
