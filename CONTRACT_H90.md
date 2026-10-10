# H90: literal single-field GFF rejection

## Scope

Two additions only: `tests/test_h90_gff_short_record_characterization.py`
and this contract. Product source and existing tests remain unchanged.

One literal `parse_gff("chr1")` call pins exact exception identity
`ValueError` and exact text `line 1: GFF record has 1 fields, need 9`.
Current field-count guard rejects before indexing. Expected text comes
from current source, not a parser oracle. No all-widths, phase-values,
line-numbering, attributes, GFF-standard, successful-parse, consumer,
model, or biology claim.

## Documentary read gate

Base: `9f2b4992cf58e07432ff35fe9ceff0ab925098d2`.
2026-10-10 IST: parent ratified scope at 23:56:33. Fresh public HTTPS
fetch at 23:56:37 confirmed 9f2b4992; full gff.py, test_bio_gff.py and
test_cli_gff.py visibly read before authoring at 23:56:51. Existing
short-record rejection uses three fields and substring `need 9`, not
this exact diagnostic. No exhaustive collision-search claim. Chronology
is author self-report, not independent certification.

## Actual author receipts

Python 3.10.12, pytest 9.1.1, existing private environment.

- New file: 1 passed (`new.xml`).
- New + test_bio_gff.py + test_cli_gff.py: 17 passed (`adjacent.xml`).
- tests/self_improve + those same three files: 1857 passed, 13 xfailed
  (`wider.xml`). This is not the global suite.
- Restored-source adjacent selection: 17 passed (`restored.xml`).

Four independent temporary parse_gff mutants fail the new test with exit 1:

1. Remove field-count guard: IndexError escapes.
2. Return None instead of raise: DID NOT RAISE ValueError.
3. Change diagnostic: text fails with `line 1: wrong field count`.
4. Change exception class to RuntimeError: exception escapes.

Each mutant started from original source; finally-block restoration,
cache removal and byte-exact source comparison were performed.
Restored gff.py SHA256:
`c3650708b855eb251c45fbcf8511a1b0e154295eb2b8eac622f952440f859feb`.
Receipt archive includes XMLs, mutant log and reproducer. Candidate/tree/
parent hashes and committed new-file blobs are in the manifest.
No mutation is committed. Separate audit and explicit publication handoff
are still required; no push is performed by this author.
