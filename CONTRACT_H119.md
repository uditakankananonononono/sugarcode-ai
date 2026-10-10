# H119: incremental literal bang GFF strand

Exactly two additions: this contract and
 tests/test_h119_gff_strand_bang_characterization.py.
One parse_gff('chr1\ta\tgene\t1\t9\t.\t!\t.\tID=g') call pins exact
ValueError identity and "line 1: invalid strand '!'". Current strand guard
93/raise94, after coordinates and before phase/attributes.
H93 strand-x and direct strand-x-newline use same guard, different literal.
H119 distinct bang literal only, not generic strand/diagnostic novelty.
H85 same diagnostic family in DIFFERENT BED module, not GFF coverage.
Source-derived diagnostic, not strand-policy oracle. No other input,
successful parsing, attributes, conformance, coordinate, consumer, model,
accuracy or biology claim. No source/existing-test edits; comments not validated.

## Read gate

Base/live public re-anchorce6d644e42fe596a0f760074579f3b8f35375594
verified2026-10-11 00:52:56 IST before authoring, after H113 landed.
Fresh full gff.py/direct/CLI tests and H93 contract visibly read. Scoped
H-test/contract search found H93 overlap and different-module H85, no same
bang literal; not exhaustive absence. Source blob
42babd534fb5f86fa916b162c17d52e34feb4bd3.
Literal probe confirmed identity/text. Parent ratified00:52:45.
Chronology is author self-report, not independent certification.

## Actual runtime

/tmp/sugar-build-venv/bin/python, explicit repository src PYTHONPATH.
New1P/.18s, new+direct+CLI17P/.54s,
same+tests/self_improve1857P/13X/38.70s. Selected, not global suite;
XFAILs not implemented repairs. Restored new1P/.15s.
Four independent new-only mutants, all1FAIL/exit1:
- ReturnNone/.14s: did not raise.
- Return full diagnostic string/.18s: did not raise.
- RuntimeError/.16s: escapes.
- Remove strand guard/.17s: accepted record, did not raise.
Each starts from original bytes; finally restoration/cache removal and
byte-equality check, final source SHA256:
c3650708b855eb251c45fbcf8511a1b0e154295eb2b8eac622f952440f859feb.
XMLs/full log/reproducer supplied with per-receipt manifest hashes.
No exhaustive mutant adequacy claim. No push; separate audit/publication required.
