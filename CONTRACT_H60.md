# H60 literal JASPAR row-prefix diagnostic

Parent: 3299a6a5dac809fc289dfe84223343c3b390dec3.
Adds only this contract and one independent test file. No product-source or
old-test edits. Pins one rejection and its diagnostic; no parsed motif,
PWM-value, format-standard, mathematical or biological claim.

## Documentary read gate and overlap

2026-10-10 IST: full motif.py, test_bio_motif.py and test_cli_motif.py visibly
read at 22:29:42. CLI loader/handlers and H52 test/contract read 22:29:53.
Repository search found no invalid-row-prefix guard test. H52 exercises
valid A prefix and bad numeric token, a different branch. Existing
before-header, missing-row and unequal-length tests are separate. No
exhaustive coverage claim. Chronology is self-report, not independent proof.

Parent ratified 22:30:03. Fresh public HTTPS fetch, unchanged parent and full
source/direct/CLI-test visible re-anchor 22:30:11 preceded test authoring.
Source blob: 34b8d56bfec47d1faedf76feac897e894e252c2c.
Direct test blob: 6c5981f4bacb29315a06bae3368bbd3d3a59f4aa.
CLI test blob: cdbad9d353d752e89e7b644bee4c738581551aff.

## Exact scope

One literal `read_jaspar(">toy\nX [ nope ]\n")` call pins exact ValueError
type and `line 2: row must start with A/C/G/T`. The X row-prefix guard fires
before attempting numeric conversion of nope. Expected message comes from
current source, not a format oracle. No other input or successful result
is asserted.

## Author receipts, independent audit still required

Python 3.10.12, pytest 9.1.1 using existing private venv/system packages.

- New file: 1 passed in 0.13s.
- New + bio_motif + CLI motif + H52: 10 passed in 0.30s.
- tests/self_improve + same four files: 1850 passed, 13 xfailed in 31.86s.
  This is not the global suite.
- Four independent temporary mutants each fail the new test: skipping
  prefix guard, permitting X, and moving guard after numeric conversion
  reach the non-numeric diagnostic; changed diagnostic fails equality.
- Source restored byte-exact, SHA256:
  74252072c1cd38b37e4fb1b1b4d9b10de9d6e872722bce0359b1d98da57a6902.
- Restored new test rerun: 1 passed in 0.14s.

No source mutation committed. Separate audit and explicit execution or
composition instruction required before publication.
