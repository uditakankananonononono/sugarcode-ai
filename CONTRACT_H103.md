# H103: literal zero-size BED block

Exactly two additions: this contract and
 tests/test_h103_bed_zero_size_characterization.py.
One parse_bed('chr1\t0\t9\tg\t0\t+\t0\t9\t0\t1\t0\t0') call pins
exact ValueError identity and
'line 1: block at +0 size 0 escapes the interval'. Count matches, first
start0; only b<1 rejects, not overshoot. Source guard67/raise68.
Existing ordinary direct regex covers 'escapes the interval' on positive
overshooting block95 at+10/end100. This is a distinct zero-size literal/clause
pin, not diagnostic novelty or generic block-policy/conformance guarantee.
No other input, successful parsing, consumer, model, accuracy or biology claim.
Source-derived diagnostic, not independent coordinate oracle.

## Read gate

Base/live public re-anchor5633f804a7d6096a1044790d41c8440bff83185c
verified2026-10-11 00:28:11 IST before authoring. Fresh full source180,
direct95, CLI44 lines visibly read. Scoped H-test/contract search for zero-size
and same suffix found no same pin; not exhaustive absence. Source blob
cdaf35e536e26de74b34b8312a8cff7ab23d57e8. Literal probe confirmed identity/text.
Parent ratified00:28:06. Chronology is author self-report, not independent
certification; comments not validated. No source or existing-test edits.

## Actual runtime

/tmp/sugar-build-venv/bin/python, explicit repository src PYTHONPATH.
New1P/.13s; new+direct+CLI16P/.38s;
same+tests/self_improve1856P/13X/37.46s, selected not global suite.
Restored new1P/.18s. XFAILs not implemented repairs.
Four independent new-only mutants, all1FAIL/exit1:
- ReturnNone/.13s: did not raise.
- Return full diagnostic text/.12s: did not raise.
- RuntimeError/.12s: escapes.
- Remove only b<1, retain overshoot/.12s: accepted record, did not raise.
Each starts from original bytes; finally restoration/cache removal and
byte-equality check, final source SHA256:
8f8a6cce995c76b9b16cf5d4df5ff661b96c4f0a1e6f9522627327bd8482e420.
XMLs/full log/reproducer supplied with per-receipt manifest hashes.
No exhaustive mutant adequacy claim. No push; separate audit/publication required.
