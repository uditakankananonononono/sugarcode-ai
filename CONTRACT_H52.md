# H52 literal JASPAR non-numeric-count diagnostic

Parent: bf1c93811db53aecbeec6fea0cd72751282ed707.
Adds only this contract and one independent test file. No product source or
old-test edits. No successful-parse, PWM-value, standard, math, or biological
validation claim.

## Documentary read gate and overlap check

2026-10-10 IST: full motif.py, test_bio_motif.py and test_cli_motif.py visibly
read at 22:08:34; full pwm.py and primer.py dependencies read at 22:08:40.
CLI motif loader/handlers read at 22:08:43. Repository coverage searches
found existing JASPAR rejection tests for row before header, missing rows,
and unequal row lengths, not this non-numeric-count branch or exact physical
line diagnostic. P05's normalized_score contract is unrelated. No exhaustive
coverage claim. Read chronology is self-report, not independently certified.

Parent ratified at 22:09:00. Fresh public HTTPS fetch, unchanged parent and
full source/direct/CLI test re-anchor at 22:09:06 preceded test authoring.
Source blob: 34b8d56bfec47d1faedf76feac897e894e252c2c.
Direct test blob: 6c5981f4bacb29315a06bae3368bbd3d3a59f4aa.
CLI test blob: cdbad9d353d752e89e7b644bee4c738581551aff.

## Exact scope

One literal `read_jaspar("\n>toy\n\nA [ nope ]\n")` call pins exact
ValueError type and `line 4: non-numeric count`. The skipped blank physical
lines still count in enumeration; the bad numeric token is on physical
line 4. Expected diagnostic comes from current source, not a format oracle.
No successful parse or other input is asserted.

## Author receipts, independent audit still required

Python 3.10.12, pytest 9.1.1 using the existing private venv/system packages.

- New file: 1 passed in 0.10s.
- New + bio_motif + CLI motif: 9 passed in 0.28s.
- tests/self_improve + same three files: 1849 passed, 13 xfailed in 30.39s.
  This is not the global suite.
- Four independent temporary source mutants each fail the new test:
  enumerate from 0 (line 3); filter blanks before enumeration (line 2);
  altered diagnostic (invalid count); zero-filled numeric conversion
  (missing-row diagnostic instead). Last mutant does not successfully parse.
- Source restored byte-exact, SHA256:
  74252072c1cd38b37e4fb1b1b4d9b10de9d6e872722bce0359b1d98da57a6902.
- Restored new test rerun: 1 passed in 0.11s.

No source mutation committed. Separate audit and explicit execution or
composition instruction required before publication.
