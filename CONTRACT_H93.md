# H93: incremental literal GFF strand identity/text

Runtime-characterized, audit/publication pending. Exactly two additions.
Authoring live-tip re-anchor4054a9909f1ebab9e62e5afa9c92bcb36739a2c5
matched local HEAD, no replay. Fresh full GFF237/direct119/CLI40 reads before
writing; source blob42babd534fb5f86fa916b162c17d52e34feb4bd3.
Strand guard92/raise93 after coordinate checks, before phase/attributes.
Probe exact ValueError and "line 1: invalid strand 'x'".
Existing test_bio_gff.py114-115 already checks invalid-strand substring for
same x and same row with a trailing newline. New literal omits that newline;
this is incremental exact exception identity/text coverage, not newly
characterized invalid-strand behavior. No exhaustive collision absence claim.
Parent explicitly assigned/ratified this incremental scope.

One direct parse_gff('chr1\ta\tgene\t1\t9\t.\tx\t.\tID=g') call,
exact ValueError identity/diagnostic. No general strand policy, line numbering,
attributes, GFF conformance, successful parsing, consumer/model/biology claims.
Source-derived pin, no external format oracle; comment provenance not validated.
No source/old-test edits; adjacent coverage does not enlarge this unit.

## Author runtime

/tmp/sugar-build-venv/bin/python, explicit repository src PYTHONPATH.
New1 passed/.12s.
Adjacent new+tests/test_bio_gff.py+tests/test_cli_gff.py:17 passed/.65s.
Wider selected same+tests/self_improve:1857 passed/13 xfailed/38.58s.
Not global suite; XFAILs not implemented repairs.
Restored new1 passed/.15s.
Four independent new-only mutants:
- Remove strand guard:1 failed/.16s (accepted dictionary).
- Guard returnNone:1 failed/.18s.
- Diagnostic 'bad strand':1 failed/.19s.
- Exception RuntimeError:1 failed/.20s.
Source byte-restored after each, final SHA256:
c3650708b855eb251c45fbcf8511a1b0e154295eb2b8eac622f952440f859feb.
XMLs/full log supplied with per-receipt hashes in manifest.
No exhaustive mutant adequacy claim. No push; separate publication required.
