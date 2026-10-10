# H85: one literal BED strand rejection

Runtime-characterized, audit/publication pending. Two additions only.
Authoring live-tip re-anchor71c5d864a962520f3916c56787a13c8e082f0e1b
matched local HEAD, no replay. Fresh full BED180/direct95/CLI44 source/test
reads before authoring; source blobcdaf35e536e26de74b34b8312a8cff7ab23d57e8.
Scoped invalid-strand/literal coverage search found GFF rejection (different
module) and prefix-schema context, no exact direct BED pin found; not exhaustive.
Current strand-membership guard43/raise44 follows coordinates and score.
Literal probe gives exact ValueError and "line 1: invalid strand 'x'".
Parent assignment explicitly ratified H85 before authoring.

Direct parse_bed('chr1\t0\t10\tx\t0\tx') single call, exact ValueError
identity plus exact diagnostic. No all-strands, normalization, general-input,
line-numbering, coordinates/score, BED conformance, successful parsing,
consumer/model/biology claims. Diagnostic source-derived, not external oracle.
No production/old-test changes. Adjacent successes do not broaden this pin.

## Author evidence

/tmp/sugar-build-venv/bin/python, explicit repository src PYTHONPATH.
New1 passed/.15s.
Adjacent new+tests/test_bio_bed.py+tests/test_cli_bed.py:16 passed/.69s.
Wider selected same+tests/self_improve:1856 passed/13 xfailed/35.07s.
Not global suite; XFAILs not implemented repairs.
Restored new1 passed/.17s.
Four independent new-only mutants from original source:
- Remove strand guard:1 failed/.15s (accepted-return).
- Guard returnNone:1 failed/.16s.
- Diagnostic 'bad strand':1 failed/.16s.
- Exception RuntimeError:1 failed/.16s.
Source byte-restored after each attempt, final SHA256:
8f8a6cce995c76b9b16cf5d4df5ff661b96c4f0a1e6f9522627327bd8482e420.
XML receipts and full log included, per-receipt hashes in manifest.
No exhaustive mutant adequacy claim; no push, separate publication required.
