# H98: exact literal blockcount conversion diagnostic

## Scope

Exactly two additions: this contract and
`tests/test_h98_bed_blockcount_conversion_characterization.py`.
Product source and existing tests unchanged.

One literal `parse_bed('chr1\t0\t9\tg\t0\t+\t0\t9\t0\tx\t9\t0')`
call pins exact exception identity `ValueError` and exact text
`line 1: malformed block fields`. The literal blockcount x triggers current
int conversion handler. Diagnostic is source-derived. No other malformed
inputs, broad block validation, format/conformance, coordinate, consumer,
model, accuracy or biology claims.

## Documentary read gate

Base `c5ae3cedc21d77f7e2542cbb72d119ff32c2f13e`.
2026-10-11 IST: parent ratified at 00:17:34; fresh public HTTPS fetch at
00:17:37 re-anchored onto c5ae3ced. Full bed.py, test_bio_bed.py and
test_cli_bed.py visibly read before authoring. Direct tests do not pin
this literal conversion diagnostic. Collision-clearance is parent/auditor
reported; no independent exhaustive search claimed. Chronology is author
self-report, not independent certification.

## Actual receipts

Python 3.10.12, pytest 9.1.1, existing private environment.

- New: 1 passed, new.xml.
- New + bio_bed + cli_bed: 16 passed, adjacent.xml.
- tests/self_improve + same three files: 1856 passed, 13 xfailed,
  wider.xml. This is not the global suite.
- Restored-source adjacent: 16 passed, restored.xml.

Four independent temporary mutants fail the new test with exit 1:

1. Return None: DID NOT RAISE ValueError.
2. Return diagnostic text: DID NOT RAISE ValueError.
3. Wrong exception class RuntimeError: escapes.
4. Remove try/except wrapper, retain conversion statements: raw int
   ValueError identity passes but diagnostic equality fails.

Each mutant starts from original bytes. Finally-block source restoration,
source cache removal and byte-exact comparison performed.
Restored bed.py SHA256:
`8f8a6cce995c76b9b16cf5d4df5ff661b96c4f0a1e6f9522627327bd8482e420`.
XML/log/reproducer archive and committed-blob manifest accompany the package.
No temporary mutations committed. Separate audit and explicit publication
handoff remain required; no push by this author.
