# H113: incremental literal two-field GFF rejection

Exactly two additions: this contract and
 tests/test_h113_gff_two_fields_characterization.py.
One parse_gff('chr1\ta') call pins exact ValueError identity and
'line 1: GFF record has 2 fields, need 9'. Count guard85/raise86 rejects
before indexing. H90 pins one-field literal on same guard; ordinary direct
regex uses three fields/need9. Parent reports reserved H111 ten-field pin
on same guard; not present on this authoring base, no runtime claim for it.
This is two-field literal only, no general field-validation novelty.
Source-derived diagnostic, not parser oracle. No other widths/input,
successful parse, attributes, line-number generality, conformance, consumer,
model, accuracy or biology claim. No source/existing-test edits; comments
not validated.

## Read gate

Base/live public re-anchor05fc2a6040ad8a49b13077a613d1e468592ec8f9
verified2026-10-11 00:48:52 IST before authoring, after H109 landed.
Fresh full gff.py/direct/CLI tests and H90 contract visibly read. Scoped
H-test/contract search found H90 count overlap, no same two-field pin;
not exhaustive absence. Source blob42babd534fb5f86fa916b162c17d52e34feb4bd3.
Literal probe confirmed identity/text. Parent ratified00:48:38.
Chronology is author self-report, not independent certification.

## Actual runtime

/tmp/sugar-build-venv/bin/python, explicit repository src PYTHONPATH.
New1P/.14s, new+direct+CLI17P/.38s,
same+tests/self_improve1857P/13X/39.56s. Selected, not global suite;
XFAILs not implemented repairs. Restored new1P/.11s.
Four independent new-only mutants, all1FAIL/exit1:
- ReturnNone/.13s: did not raise.
- Return full diagnostic string/.13s: did not raise.
- RuntimeError/.15s: escapes.
- Remove field-count guard/.21s: IndexError at f[3], not accepted record.
Each starts from original bytes; finally restoration/cache removal and
byte-equality check, final source SHA256:
c3650708b855eb251c45fbcf8511a1b0e154295eb2b8eac622f952440f859feb.
XMLs/full log/reproducer supplied with per-receipt manifest hashes.
No exhaustive mutant adequacy claim. No push; separate audit/publication required.
