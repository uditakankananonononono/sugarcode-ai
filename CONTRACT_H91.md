# H91: literal invalid GFF phase rejection

Runtime-characterized, audit/publication pending. Two additions only.
Authoring live-tip re-anchor9f2b4992cf58e07432ff35fe9ceff0ab925098d2
matched local HEAD, no replay. Fresh full GFF237/direct119/CLI40 reads before
writing; source blob42babd534fb5f86fa916b162c17d52e34feb4bd3.
Scoped phase/literal coverage search found different coordinate/strand inputs,
no exact phase literal pin found; not exhaustive coverage absence.
Phase guard94/raise95 after coordinate/strand checks, before attributes96.
Literal probe exact ValueError and "line 1: invalid phase 'x'".
Parent assignment explicitly ratified H91; no source/old-test changes.

Direct single call parse_gff('chr1\ta\tgene\t1\t9\t.\t+\tx\tID=g'),
exact ValueError identity plus exact diagnostic. No all-phase-values,
line numbering, attributes, GFF standard, successful parsing, consumer,
model or biology claims. Source-derived diagnostic, no external format oracle.
Source comments/provenance not independently validated by this unit.

## Author runtime

/tmp/sugar-build-venv/bin/python, explicit repository src PYTHONPATH.
New1 passed/.13s.
Adjacent new+tests/test_bio_gff.py+tests/test_cli_gff.py:17 passed/.98s.
Wider selected same+tests/self_improve:1857 passed/13 xfailed/35.76s.
Not global suite; XFAILs not implemented repairs.
Restored new1 passed/.17s.
Four independent new-only mutants from original bytes:
- Remove phase guard:1 failed/.15s. Later int('x') raises raw ValueError;
  identity still matches, exact diagnostic differs, not accepted-return here.
- Guard returnNone:1 failed/.15s.
- Diagnostic 'bad phase':1 failed/.16s.
- Exception RuntimeError:1 failed/.19s.
Source byte-restored after each attempt, final SHA256:
c3650708b855eb251c45fbcf8511a1b0e154295eb2b8eac622f952440f859feb.
XML receipts/full log supplied with per-receipt hashes in manifest.
No exhaustive mutant adequacy claim. No push, separate publication required.
