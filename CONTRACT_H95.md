# H95: literal malformed second GFF3 item

Runtime-characterized, audit/publication pending. Exactly two additions.
Authoring live-tip re-anchor369a349467ac7aa299e8b99abfc479e94e9dca18
matched local HEAD, no replay. Fresh full GFF237/direct119/CLI40 reads before
writing; source blob42babd534fb5f86fa916b162c17d52e34feb4bd3.
Scoped malformed-GFF3/literal search found no direct exact pin for this input;
not exhaustive coverage absence. First ID=g selects GFF3 branch; second bad
item lacks equals, guard61/raise62 precedes split63. Literal probe exact
ValueError and "line 1: malformed GFF3 attribute 'bad'".
Parent explicitly assigned and ratified H95 before authoring.

One direct parse_gff('chr1\ta\tgene\t1\t9\t.\t+\t.\tID=g;bad') call,
exact ValueError identity and diagnostic. No other malformed inputs, general
attribute parsing, GFF conformance, successful parsing, consumer/model/biology
claims. Source-derived diagnostic, not external parser oracle. No production
or old-test edits; source comment provenance not validated by this unit.

## Author runtime

/tmp/sugar-build-venv/bin/python, explicit repository src PYTHONPATH.
New1 passed/.13s.
Adjacent new+tests/test_bio_gff.py+tests/test_cli_gff.py:17 passed/.68s.
Wider selected same+tests/self_improve:1857 passed/13 xfailed/35.01s.
Not global suite; XFAILs not implemented repairs.
Restored new1 passed/.14s.
Four independent new-only mutants:
- Missing-equals guard returnNone:1 failed/.16s; caller tuple unpack TypeError.
- Diagnostic 'bad GFF3 attribute':1 failed/.16s.
- Exception RuntimeError:1 failed/.17s.
- Remove missing-equals guard:1 failed/.15s; split unpack raw ValueError,
  identity matches but exact diagnostic differs.
Source byte-restored after each attempt, final SHA256:
c3650708b855eb251c45fbcf8511a1b0e154295eb2b8eac622f952440f859feb.
XMLs/full log supplied, per-receipt hashes in manifest.
No exhaustive mutant adequacy claim. No push; separate publication required.
