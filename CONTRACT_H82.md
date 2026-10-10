# H82: literal single-field BED rejection

## Scope

Two additions only: `tests/test_h82_bed_short_record_characterization.py`
and this contract. Product source and existing tests remain unchanged.

One literal `parse_bed("chr1")` call pins exact exception type `ValueError`
and exact text `line 1: BED record has 1 fields, need >= 3`.
Current minimum-fields guard rejects before coordinate indexing. Expected
text comes from current source, not a parser oracle. No all-short-widths,
line-numbering, tab-semantics, coordinates, successful-parse, BED-standard,
consumer, model, or biology claim. H81's empty no-record guard is distinct.

## Documentary read gate

Base: `fa082dff15f1847e46e3aed1a4a58c66b4d990e2`.
2026-10-10 IST: parent ratified scope at 23:37:28 and directed current-tip
re-anchor. Fresh public HTTPS fetch at 23:37:33 found fa082dff, with H81
present. Full bed.py, test_bio_bed.py and test_cli_bed.py visibly read;
relevant CLI consumers inspected and repository coverage searched.
Related test_bed_prefix_schema_prep.py read in full at 23:37:45 before
authoring. Its short-width tests call the separate prefix parser; its
product-parser canaries are widths 7/10/11, distinct from this literal.
No existing exact single-field product diagnostic pin was found. No
exhaustive coverage claim. Chronology is author self-report, not independent
certification. The parent message's escaped >= is used as literal >=.

## Actual author receipts

Python 3.10.12, pytest 9.1.1, existing private environment.

- New file: 1 passed (`new.xml`).
- New + test_bio_bed.py + test_cli_bed.py: 16 passed (`adjacent.xml`).
- tests/self_improve + those same three files: 1856 passed, 13 xfailed
  (`wider.xml`). This is not the global suite.
- Restored-source adjacent selection: 16 passed (`restored.xml`).

Four independent temporary parse_bed mutants fail the new test with exit 1:

1. Remove minimum-fields guard: IndexError escapes.
2. Return None instead of raise: DID NOT RAISE ValueError.
3. Change diagnostic: exact text fails with `line 1: too few fields`.
4. Change exception class to RuntimeError: exception escapes.

Each mutant started from original source; finally-block restoration,
cache removal and byte-exact source comparison were performed.
Restored bed.py SHA256:
`8f8a6cce995c76b9b16cf5d4df5ff661b96c4f0a1e6f9522627327bd8482e420`.
Receipt archive includes XMLs, mutant log and reproducer. Candidate/tree/
parent hashes and committed new-file blobs are in the manifest.
No mutation is committed. Separate audit and explicit publication handoff
are still required; no push is performed by this author.
