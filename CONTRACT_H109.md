# H109: incremental literal noninteger GFF end

Exactly two additions: this contract and
 tests/test_h109_gff_noninteger_end_characterization.py.
One parse_gff('chr1\ta\tgene\t1\tx\t.\t+\t.\tID=g') call pins exact
ValueError identity and 'line 1: start/end not integers'. Start1 converts;
end-x int fails on second operand at88, handler89/raise90. H94 pins start-x
on same handler/diagnostic; ordinary direct regex pins start-x with newline.
H109 distinct end-x literal only, not generic conversion/diagnostic novelty.
H83 same diagnostic in DIFFERENT BED module, not GFF operand coverage.
Source-derived diagnostic, not integer-policy oracle. No other input,
successful parsing, attributes parsing, conformance, coordinate, consumer,
model, accuracy or biology claim. No source/existing-test edits; comments
not validated.

## Read gate

Base/live public re-anchorc39c761c0334654a34804adc7d60b4f51b2fec74
verified2026-10-11 00:44:33 IST before authoring. Fresh full gff.py,
direct/CLI tests and H94 contract visibly read. Scoped H-test/contract search
found H94 overlap and different-module H83; no same GFF end-x pin, not
exhaustive absence. Source blob42babd534fb5f86fa916b162c17d52e34feb4bd3.
Literal probe confirmed identity/text. Parent ratified00:44:28.
Chronology is author self-report, not independent certification.

## Actual runtime

/tmp/sugar-build-venv/bin/python, explicit repository src PYTHONPATH.
New1P/.17s, new+direct+CLI17P/.48s,
same+tests/self_improve1857P/13X/41.14s. Selected, not global suite;
XFAILs not implemented repairs. Restored new1P/.12s.
Four independent new-only mutants, all1FAIL/exit1:
- ReturnNone/.14s: did not raise.
- Return full diagnostic string/.14s: did not raise.
- RuntimeError/.16s: escapes.
- Remove try/except wrapper, retain conversion/.19s: raw int ValueError
  identity passes, diagnostic equality fails.
Each starts from original bytes; finally restoration/cache removal and
byte-equality check, final source SHA256:
c3650708b855eb251c45fbcf8511a1b0e154295eb2b8eac622f952440f859feb.
XMLs/full log/reproducer supplied with per-receipt manifest hashes.
No exhaustive mutant adequacy claim. No push; separate audit/publication required.
