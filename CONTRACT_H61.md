# H61 literal unknown-model diagnostic

Parent: 8360ec272b7b95e812d33bf55591b806dbfb450f.
Adds only this contract and one independent test file. No product-source or
old-test edits. Pins one rejection diagnostic, not successful matrices or
model-accuracy/evolutionary/biological behavior.

## Documentary read gate and overlap

2026-10-10 IST: full phylo.py, test_bio_phylo.py and test_cli_phylo_trees.py
visibly read at 22:35:38; CLI dist/build consumers and repository coverage
search read in the same call. Existing test rejects jc85 with two sequences,
but does not pin exact diagnostic, sorted key list, repr quoting or the
empty-input path. No stronger relevant pin found; no exhaustive coverage
claim. Read chronology is self-report, not independent certification.

Parent ratified 22:35:55. Fresh public HTTPS fetch, unchanged parent and full
source/direct/CLI-test visible re-anchor 22:36:02 preceded authoring.
Source blob: 5494887d00214e3b8f312ab2464922ab1d47797d.
Direct test blob: 8a62b2f092214165bbf202b3da1aeba06a2d53dc.
CLI test blob: e0831d75024f051f0728919175941d3ff40a2001.

## Exact scope

One literal `distance_matrix({}, "bad")` call pins exact ValueError type
and `model must be one of ['jc69', 'k80', 'pdistance'], got 'bad'`.
The model guard rejects even with empty input before matrix work, and its
message lists sorted keys and repr-quotes the invalid model. Expectations
come from current source, not a model oracle. No successful empty-matrix
return or other input is asserted.

## Author receipts, independent audit still required

Python 3.10.12, pytest 9.1.1 using existing private venv/system packages.

- New file: 1 passed in 0.08s.
- New + bio_phylo + CLI phylo_trees + H54: 16 passed in 0.60s.
- tests/self_improve + same four files: 1856 passed, 13 xfailed in 33.96s.
  This is not the global suite.
- Four independent temporary distance_matrix-scoped mutants each fail:
  skipped guard causes KeyError; insertion-order listing, omitted repr
  quoting and changed prefix each fail diagnostic equality.
- Source restored byte-exact, SHA256:
  0a5c47e67621a0c7ad552b1e5390cdb857304725cea08b9c2a55579750dcacc5.
- Restored new test rerun: 1 passed in 0.15s.

No source mutation committed. Separate audit and explicit execution or
composition instruction required before publication.
