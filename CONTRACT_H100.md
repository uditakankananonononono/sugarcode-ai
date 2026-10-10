# H100: literal reversed thick endpoints

## Scope and overlap disclosure

Exactly two additions: this contract and
`tests/test_h100_bed_reversed_thick_characterization.py`.
Product source and existing tests unchanged.

One `parse_bed('chr1\t0\t9\tg\t0\t+\t5\t4')` call pins exact
ValueError identity and `line 1: thick block outside the interval` text.
Only ts > te rejects: ts=5 >= start=0 and te=4 <= end=9.
H97 pins ts < start with -1,9; H99 pins te > end with 0,10.
This is the third distinct literal/clause, not diagnostic novelty or a
general thick-block guarantee. Source-derived diagnostic, no external
coordinate oracle. No other inputs, successful parsing, format/conformance,
consumer, model, accuracy or biology claims.

## Documentary read gate

Base: `77750cba98688c6078fac342c6c9876632f8514d`.
2026-10-11 IST: parent ratified 00:22:33; public HTTPS fetch 00:22:38
re-anchored onto 77750cba. Full bed.py, direct and CLI tests, H97/H99
contracts visibly read before authoring. Direct tests do not pin this
literal. H97/H99 overlap disclosed above. No exhaustive collision-search
claim. Read chronology is author self-report, not independent certification.

## Actual receipts

Python 3.10.12, pytest 9.1.1, existing private environment.

- New: 1 passed, new.xml.
- New + bio_bed + cli_bed: 16 passed, adjacent.xml.
- tests/self_improve + same three files: 1856 passed, 13 xfailed,
  wider.xml. Selected suite, not global suite.
- Restored-source adjacent: 16 passed, restored.xml.

Four independent temporary mutants fail the new test with exit 1:

1. Return None at guard: DID NOT RAISE ValueError.
2. Return text at guard: DID NOT RAISE ValueError.
3. RuntimeError class: escapes.
4. Remove only ts > te clause, retain other clauses: returns a record,
   DID NOT RAISE ValueError.

Each mutant starts from original bytes. Finally-block source restoration,
source cache removal and byte-exact comparison performed.
Restored bed.py SHA256:
`8f8a6cce995c76b9b16cf5d4df5ff661b96c4f0a1e6f9522627327bd8482e420`.
Archive includes XML, log and reproducer. Manifest supplies candidate,
parent, tree and committed new-file blobs. No mutations committed.
Separate audit and publication handoff required; no push by this author.
