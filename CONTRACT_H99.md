# H99: literal thick end after BED interval

Runtime-characterized, audit/publication pending. Exactly two additions.
Authoring live-tip re-anchorc5ae3cedc21d77f7e2542cbb72d119ff32c2f13e
matched local HEAD, no landing work in flight/no replay. Fresh full BED180/
direct95/CLI44/H97 test reads before writing; source blob
cdaf35e536e26de74b34b8312a8cff7ab23d57e8.
Scoped thick/literal H-test search finds H97 exact same diagnostic but input
has ts=-1,te=9 (ts<start). H99 uses ts=0,te=10, so only te>end rejects;
other clauses false. Different clause/literal, no generic diagnostic novelty.
No exhaustive collision absence claim. Guard48/raise49. Probe exact ValueError
and 'line 1: thick block outside the interval'. Parent ratified H99.

One direct parse_bed('chr1\t0\t9\tg\t0\t+\t0\t10') call, exact
ValueError identity and diagnostic. No general thick-block/coordinate policy,
other input, successful parsing, consumer/model/biology claims. No production
or old-test edits, source-derived pin not external coordinate oracle.
Source comments/provenance not independently validated.

## Author evidence

/tmp/sugar-build-venv/bin/python, explicit repository src PYTHONPATH.
New1 passed/.15s.
Adjacent new+tests/test_bio_bed.py+tests/test_cli_bed.py:16 passed/.47s.
Wider selected same+tests/self_improve:1856 passed/13 xfailed/40.55s.
Not global suite; XFAILs not implemented repairs.
Restored new1 passed/.15s.
Four independent new-only mutants:
- Guard returnNone:1 failed/.15s.
- Guard returns diagnostic string instead of raising:1 failed/.16s.
- Exception RuntimeError:1 failed/.16s.
- Remove te>end, retain ts<start/ts>te:1 failed/.15s (record returned).
Source byte-restored after each, final SHA256:
8f8a6cce995c76b9b16cf5d4df5ff661b96c4f0a1e6f9522627327bd8482e420.
XMLs/full log supplied with per-receipt hashes in manifest.
No exhaustive mutant adequacy claim. No push; separate publication required.
