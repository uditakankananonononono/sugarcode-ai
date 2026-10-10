# H108: literal end-x BED conversion pin

## Scope and overlap

Exactly two additions: this contract and
`tests/test_h108_bed_end_conversion_characterization.py`.
Source and existing tests unchanged.

One `parse_bed('chr1\t0\tx')` call pins exact ValueError type and
`line 1: start/end not integers` text. Three fields reach conversion;
start0 converts, end-x fails. H83 pins same handler/diagnostic on start-x
with `chr1\tx\t10`. H108 is end-x literal only, no generic diagnostic
novelty. Source-derived diagnostic, not external format oracle. No other
inputs, successful parsing, general conversion/policy, format/conformance,
coordinate, consumer, model, accuracy or biology claims.

## Documentary read gate

Base `c39c761c0334654a34804adc7d60b4f51b2fec74`.
2026-10-11 IST: parent ratified at 00:44:28; public HTTPS fetch at 00:44:32
re-anchored onto c39c761c. Full bed.py, direct/CLI tests and H83 contract
visibly read before authoring. Shared H83 diagnostic disclosed above.
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
2. Return diagnostic string: DID NOT RAISE ValueError.
3. RuntimeError class: escapes.
4. Remove try/except wrapper, retain conversion: raw int ValueError
   passes exact type but fails diagnostic equality.

Each mutant starts from original bytes. Finally-block source restoration,
source cache removal and byte-exact comparison performed.
Restored bed.py SHA256:
`8f8a6cce995c76b9b16cf5d4df5ff661b96c4f0a1e6f9522627327bd8482e420`.
Archive includes XML/log/reproducer; manifest supplies candidate, tree,
parent and committed addition blobs. No mutations committed. Separate
audit/publication handoff required; no push by this author.
