# H92: literal zero-start GFF rejection

## Scope

Two additions only: `tests/test_h92_gff_zero_start_characterization.py`
and this contract. Product source and existing tests remain unchanged.

One literal `parse_gff("chr1\ta\tgene\t0\t9\t.\t+\t.\tID=g")` call
pins exact exception identity `ValueError` and exact text
`line 1: invalid coordinates 0..9`. Current zero-start clause rejects
before later fields are processed. Expected text comes from current source,
not a coordinate oracle. No general coordinate policy, line-numbering,
attributes, GFF conformance, successful-parse, consumer, model, or biology.

## Documentary read gate

Base: `4054a9909f1ebab9e62e5afa9c92bcb36739a2c5`.
2026-10-11 IST: parent ratified scope at 00:00:59. Fresh public HTTPS
fetch at 00:01:14 found 4054a990; full gff.py, test_bio_gff.py and
test_cli_gff.py visibly read before authoring. Existing invalid-coordinate
rejection uses inverted 9..5 and substring matching, distinct from zero
start. No exhaustive collision-search claim. Chronology is author
self-report, not independent certification.

## Actual author receipts

Python 3.10.12, pytest 9.1.1, existing private environment.

- New file: 1 passed (`new.xml`).
- New + test_bio_gff.py + test_cli_gff.py: 17 passed (`adjacent.xml`).
- tests/self_improve + those same three files: 1857 passed, 13 xfailed
  (`wider.xml`). This is not the global suite.
- Restored-source adjacent selection: 17 passed (`restored.xml`).

Four independent temporary parse_gff mutants fail the new test with exit 1:

1. Remove start<1 clause retaining end<start: DID NOT RAISE ValueError.
2. Return None instead of raise: DID NOT RAISE ValueError.
3. Change diagnostic: text fails with `line 1: bad coordinates 0..9`.
4. Change exception class to RuntimeError: exception escapes.

Each mutant started from original source and changed parse_gff only;
finally-block restoration, cache removal and byte-exact comparison done.
Restored gff.py SHA256:
`c3650708b855eb251c45fbcf8511a1b0e154295eb2b8eac622f952440f859feb`.
Receipt archive includes XMLs, mutant log and reproducer. Candidate/tree/
parent hashes and committed new-file blobs are in the manifest.
No mutation is committed. Separate audit and explicit publication handoff
are still required; no push is performed by this author.
