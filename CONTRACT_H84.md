# H84: literal negative-start BED rejection

## Scope

Two additions only: `tests/test_h84_bed_negative_start_characterization.py`
and this contract. Product source and existing tests remain unchanged.

One literal `parse_bed("chr1\t-1\t10")` call pins exact exception type
`ValueError` and exact text `line 1: invalid 0-based interval -1..10`.
Three fields and integer conversion pass, then the negative-start part
of the interval guard rejects. Expected text comes from current source,
not a coordinate oracle. No all-coordinates, normalization, BED conformance,
successful-parse, consumer, model, or biology claim.

## Documentary read gate

Base: `71c5d864a962520f3916c56787a13c8e082f0e1b`.
2026-10-10 IST: parent ratified scope at 23:43:11. Fresh public HTTPS
fetch at 23:43:25 confirmed 71c5d864; full bed.py, test_bio_bed.py and
test_cli_bed.py visibly read before authoring. Scoped H8 test/contract
coverage searched: H81 empty, H82 short field and H83 noninteger start
are distinct. Existing bio_bed interval rejection uses equal start/end,
not negative start. No exact negative-start pin found in those reads.
No exhaustive coverage claim. Related prefix tests and relevant CLI
consumers were read for H82; no fresh consumer-read claim here. Chronology
is author self-report, not independent certification.

## Actual author receipts

Python 3.10.12, pytest 9.1.1, existing private environment.

- New file: 1 passed (`new.xml`).
- New + test_bio_bed.py + test_cli_bed.py: 16 passed (`adjacent.xml`).
- tests/self_improve + those same three files: 1856 passed, 13 xfailed
  (`wider.xml`). This is not the global suite.
- Restored-source adjacent selection: 16 passed (`restored.xml`).

Four independent temporary parse_bed mutants fail the new test with exit 1:

1. Omit negative-start guard while retaining end<=start: DID NOT RAISE.
2. Return None instead of raise: DID NOT RAISE ValueError.
3. Change diagnostic: exact text fails with `line 1: bad interval -1..10`.
4. Change exception class to RuntimeError: exception escapes.

Each mutant started from original source and affected parse_bed only;
finally-block restoration, cache removal and byte-exact comparison done.
Restored bed.py SHA256:
`8f8a6cce995c76b9b16cf5d4df5ff661b96c4f0a1e6f9522627327bd8482e420`.
Receipt archive includes XMLs, mutant log and reproducer. Candidate/tree/
parent hashes and committed new-file blobs are in the manifest.
No mutation is committed. Separate audit and explicit publication handoff
are still required; no push is performed by this author.
