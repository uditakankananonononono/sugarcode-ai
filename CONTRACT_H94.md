# H94: incremental exact noninteger-start diagnostic

## Scope

Two additions only: `tests/test_h94_gff_noninteger_start_characterization.py`
and this contract. Product source and existing tests remain unchanged.

One literal `parse_gff("chr1\ta\tgene\tx\t9\t.\t+\t.\tID=g")` call
pins exact exception identity `ValueError` and exact text
`line 1: start/end not integers`. Existing bio_gff uses this same row with
a trailing newline and regex `not integers`. This adds exact identity/text,
not new conversion behavior. Expected text comes from current source, not
an integer-policy oracle. No other malformed inputs, attributes parsing,
coordinate/general format, GFF conformance, consumer, model, or biology.

## Documentary read gate

Base: `369a349467ac7aa299e8b99abfc479e94e9dca18`.
2026-10-11 IST: parent ratified scope at 00:06:20. Fresh public HTTPS
fetch at 00:06:34 confirmed 369a3494; full gff.py, test_bio_gff.py and
test_cli_gff.py visibly read before authoring. Existing regex overlap is
explicit above. No exhaustive collision-search claim. Chronology is
author self-report, not independent certification.

## Actual author receipts

Python 3.10.12, pytest 9.1.1, existing private environment.

- New file: 1 passed (`new.xml`).
- New + test_bio_gff.py + test_cli_gff.py: 17 passed (`adjacent.xml`).
- tests/self_improve + those same three files: 1857 passed, 13 xfailed
  (`wider.xml`). This is not the global suite.
- Restored-source adjacent selection: 17 passed (`restored.xml`).

Four independent temporary parse_gff mutants fail the new test with exit 1:

1. Return None from the conversion handler: DID NOT RAISE ValueError.
2. Change diagnostic: text fails with `line 1: bad integers`.
3. Change exception class to RuntimeError: exception escapes.
4. Bypass conversion with start,end=0,9: later guard gives
   `line 1: invalid coordinates 0..9`, fails exact text.

Each mutant started from original source; finally-block restoration,
cache removal and byte-exact comparison performed.
Restored gff.py SHA256:
`c3650708b855eb251c45fbcf8511a1b0e154295eb2b8eac622f952440f859feb`.
Receipt archive includes XMLs, mutant log and reproducer. Candidate/tree/
parent hashes and committed new-file blobs are in the manifest.
No mutation is committed. Separate audit and explicit publication handoff
are still required; no push is performed by this author.
