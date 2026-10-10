# H101: incremental literal BED block-count mismatch

Runtime-characterized, audit/publication pending. Exactly two additions.
Authoring live-tip re-anchor77750cba98688c6078fac342c6c9876632f8514d
matched local HEAD, no replay. Fresh full BED180/direct95/CLI44 reads before
writing; source blobcdaf35e536e26de74b34b8312a8cff7ab23d57e8.
Count guard59/raise60-62: bc2,sizes[9],starts[0]. Probe exact ValueError and
'line 1: blockCount 2 != 1 sizes / 1 starts'. Existing ordinary direct-BED
regex already covers 'blockCount 2 != 1 sizes' on another literal (end100,
size10,starts0,15). This is incremental exact identity/full-text on THIS
literal, no generic block-validation novelty. Scoped H-test search found no
same literal pin; not exhaustive coverage absence. Parent ratified H101.

One direct parse_bed('chr1\t0\t9\tg\t0\t+\t0\t9\t0\t2\t9\t0') call,
exact ValueError identity/diagnostic. No general block/count policy, other
input, BED conformance, successful parsing, consumer/model/biology claims.
Source-derived pin, not independent block oracle. No source/old-test edits;
comment provenance not validated. Adjacent success does not enlarge this pin.

## Author evidence

/tmp/sugar-build-venv/bin/python, explicit repository src PYTHONPATH.
New1 passed/.12s.
Adjacent new+tests/test_bio_bed.py+tests/test_cli_bed.py:16 passed/.39s.
Wider selected same+tests/self_improve:1856 passed/13 xfailed/36.31s.
Not global suite; XFAILs not implemented repairs.
Restored new1 passed/.14s.
Four independent new-only mutants:
- Count guard returnNone:1 failed/.17s.
- Count guard returns full diagnostic string:1 failed/.16s.
- Exception RuntimeError:1 failed/.17s.
- Remove count guard:1 failed/.16s (record returned).
Source byte-restored after each, final SHA256:
8f8a6cce995c76b9b16cf5d4df5ff661b96c4f0a1e6f9522627327bd8482e420.
XMLs/full log supplied with per-receipt hashes in manifest.
No exhaustive mutant adequacy claim. No push; separate publication required.
