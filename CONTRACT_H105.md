# H105: incremental literal BED size conversion

Exactly two additions: this contract and
 tests/test_h105_bed_size_conversion_characterization.py.
One parse_bed('chr1\t0\t9\tg\t0\t+\t0\t9\t0\t1\tx\t0') call pins
exact ValueError identity and 'line 1: malformed block fields'. Blockcount1
converts at55; size-list x fails int at56, before starts conversion57,
handler58/raise59. H98 pins SAME diagnostic/handler on blockcount-x literal.
H105 is incremental exact identity/full text on THIS literal/different
conversion operand only, no generic diagnostic novelty or block policy.
Source-derived diagnostic, not external format oracle. No other input,
successful parsing, conformance, coordinate, consumer, model, accuracy or
biology claims. No source or existing-test edits; comments not validated.

## Read gate

Base/live public re-anchor3f95dd5bfd0b332157699a75a0afdb33ef7db6ef
verified2026-10-11 00:33:25 IST before authoring. Fresh full source180,
direct95/CLI44 and H98 test/contract visibly read. Scoped H-test/contract
search found H98 shared diagnostic, no same size-x literal; not exhaustive
absence. Source blobcdaf35e536e26de74b34b8312a8cff7ab23d57e8.
Literal probe confirmed identity/text. Parent ratified00:33:20.
Chronology is author self-report, not independent certification.

## Actual runtime

/tmp/sugar-build-venv/bin/python, explicit repository src PYTHONPATH.
New1P/.13s; new+direct+CLI16P/.37s;
same+tests/self_improve1856P/13X/37.16s, selected not global suite.
Restored new1P/.11s. XFAILs not implemented repairs.
Four independent new-only mutants, all1FAIL/exit1:
- ReturnNone/.13s: did not raise.
- Return full diagnostic text/.12s: did not raise.
- RuntimeError/.13s: escapes.
- Remove try/except wrapper, retain conversion statements/.12s:
  raw int ValueError identity passes, diagnostic equality fails.
Each starts from original bytes; finally restoration/cache removal and
byte-equality check, final source SHA256:
8f8a6cce995c76b9b16cf5d4df5ff661b96c4f0a1e6f9522627327bd8482e420.
XMLs/full log/reproducer supplied with per-receipt manifest hashes.
No exhaustive mutant adequacy claim. No push; separate audit/publication required.
