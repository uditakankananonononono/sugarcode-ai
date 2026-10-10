# H56 literal mixed-sign size-factor guard diagnostic

Parent: 8cb0b503a220718c656949099a1dc9dfaba04e05.
Adds only this contract and one independent test file. No product-source or
old-test edits. Pins one guard branch and its diagnostic, not successful
normalization values or statistical/biological accuracy.

## Documentary read gate and overlap

2026-10-10 IST: full rnaseq.py, test_bio_rnaseq.py and test_cli_rnaseq.py
visibly read at 22:19:46; full de.py consumer and CLI rnaseq handlers read
22:19:56. Repository search found existing size_factors empty/ragged/no-positive
rejections but no negative-count guard test. parse_counts negative rejection
is a different branch; H45 empty-gene diagnostic is unrelated. No exhaustive
coverage claim. Read chronology is self-report, not independently certified.

Parent ratified 22:20:08. Fresh public HTTPS fetch, unchanged parent and full
source/direct/CLI-test visible re-anchor at 22:20:15 preceded test authoring.
Source blob: cd83af0b2cfd56c4db471bc352d64151e1c524f6.
Direct test blob: cdee1ba4ea013a429728936a852c447d10c54fd0.
CLI test blob: fbb50ccf96863cda4fff246dc20e5909dd0c313b.

## Exact scope

One literal `size_factors([[1, -1]])` call pins exact ValueError type and
`negative count` diagnostic. The mixed-sign row triggers any(v<0) before
all-positive-row selection could reject it for a different reason. Expected
message comes from current source, not a normalization oracle. No other
input or successful return is asserted.

## Author receipts, independent audit still required

Python 3.10.12, pytest 9.1.1 using existing private venv/system packages.

- New file: 1 passed in 0.08s.
- New + bio_rnaseq + CLI rnaseq + bio_de + CLI de: 24 passed in 1.00s.
- tests/self_improve + same five files: 1864 passed, 13 xfailed in 32.25s.
  This is not the global suite.
- Four independent temporary mutants scoped to size_factors each fail the
  new test: removed guard, any-to-all, and threshold <-1 reach the
  no-positive-gene diagnostic; changed diagnostic returns invalid count.
- Source restored byte-exact, SHA256:
  32648ec08a7385873dbf9c659209c09bc2dffee3a96e526be3e0d7c1095cf7f4.
- Restored new test rerun: 1 passed in 0.12s.

No source mutation committed. Separate audit and explicit execution or
composition instruction required before publication.
