# H88: literal negative-query BED rejection

## Scope

Two additions only: `tests/test_h88_bed_negative_query_characterization.py`
and this contract. Product source and existing tests remain unchanged.

One literal `overlaps({"chrom":"chr1","start":0,"end":10}, "chr1", -1, 10)`
call pins exact exception identity `ValueError` and exact text
`invalid query interval -1..10`. Negative-start clause rejects before the
return expression. Expected text comes from current source, not an overlap
oracle. No overlap computation, general coordinates, other-record,
consumer, model, or biology claim.

## Documentary read gate

Base: `bc77bfa5d05703b6708aa58de1046f975b0e38de`.
2026-10-10 IST: parent ratified scope at 23:50:57. Fresh public HTTPS
fetch at 23:51:10 found bc77bfa5; full bed.py, test_bio_bed.py and
test_cli_bed.py visibly read before authoring. Existing overlaps rejection
uses equal start/end 5,5 without exact type/text pin, not negative start.
No exhaustive collision-search claim. Chronology is author self-report,
not independent certification.

## Actual author receipts

Python 3.10.12, pytest 9.1.1, existing private environment.

- New file: 1 passed (`new.xml`).
- New + test_bio_bed.py + test_cli_bed.py: 16 passed (`adjacent.xml`).
- tests/self_improve + those same three files: 1856 passed, 13 xfailed
  (`wider.xml`). This is not the global suite.
- Restored-source adjacent selection: 16 passed (`restored.xml`).

Four independent temporary overlaps mutants fail the new test with exit 1:

1. Remove negative clause while retaining end<=start: DID NOT RAISE.
2. Return None instead of raise: DID NOT RAISE ValueError.
3. Change diagnostic: text fails with `bad query interval -1..10`.
4. Change exception class to RuntimeError: exception escapes.

Each mutant started from original source and changed overlaps only;
finally-block restoration, cache removal and byte-exact comparison done.
Restored bed.py SHA256:
`8f8a6cce995c76b9b16cf5d4df5ff661b96c4f0a1e6f9522627327bd8482e420`.
Receipt archive includes XMLs, mutant log and reproducer. Candidate/tree/
parent hashes and committed new-file blobs are in the manifest.
No mutation is committed. Separate audit and explicit publication handoff
are still required; no push is performed by this author.
