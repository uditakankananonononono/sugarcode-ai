# H87: literal invalid merge distance rejection

Runtime-characterized, audit/publication pending. Two additions only.
Authoring live-tip re-anchor08fb03bd9a8345df47de1ba598301d7c272bc27c
matched local HEAD, no replay. Full fresh BED180/direct95/CLI44 reads before
writing; H49 nested-merge test read separately. Source blob
cdaf35e536e26de74b34b8312a8cff7ab23d57e8.
merge_intervals defined107, lower-bound guard115/raise116 before grouping.
Scoped merge-name/diagnostic search found bio_bed nonempty records min_dist=-2
with nonexact raises and H49 nested success literal; no exact empty-record
invalid-distance identity/text pin found. Not exhaustive coverage absence.
Probe gives exact ValueError and 'min_dist must be >= -1'. Parent assigned
and ratified H87; escaped >= in assignment interpreted as literal >=.

One direct merge_intervals([], min_dist=-2) call, exact ValueError identity
and diagnostic equality. No general distance bounds/empty-record inputs,
interval merging, coordinate semantics, successful merging, consumer/model/
biology claims. Source-derived rejection, not an external interval oracle.
No source or old-test changes; comment provenance not independently validated.

## Author evidence

/tmp/sugar-build-venv/bin/python, explicit repository src PYTHONPATH.
New1 passed/.13s.
Adjacent new+tests/test_bio_bed.py+tests/test_cli_bed.py:16 passed/.75s.
Wider selected same+tests/self_improve:1856 passed/13 xfailed/40.97s.
Not global suite; XFAILs not implemented repairs.
Restored new1 passed/.15s.
Four independent new-only mutants from original bytes:
- Remove lower-bound guard:1 failed/.16s (returns []).
- Guard returnNone:1 failed/.16s.
- Diagnostic 'invalid merge distance':1 failed/.19s.
- Exception RuntimeError:1 failed/.17s.
Source byte-restored after each attempt, final SHA256:
8f8a6cce995c76b9b16cf5d4df5ff661b96c4f0a1e6f9522627327bd8482e420.
XMLs/full log supplied with per-receipt hashes in manifest.
No exhaustive mutant adequacy claim; no push, separate verdict/publication needed.
