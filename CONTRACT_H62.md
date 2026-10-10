# H62 literal zero-min-samples diagnostic

Parent: df2cdce597707413209eb30dc22bd9b87ae63f6e.
Adds only this contract and one independent test file. No product-source or
old-test edits. Pins the lower min_samples guard and diagnostic only;
no successful-filter, normalization or biological claim.

## Documentary read gate and overlap

2026-10-10 IST: full rnaseq.py, test_bio_rnaseq.py and test_cli_rnaseq.py
visibly read at 22:42:06; relevant CLI handler and repository coverage search
read in the same call. Existing min_samples=3 test has two samples, so tests
the upper-bound side, not min_samples=0; no exact lower-bound diagnostic pin
found. No exhaustive coverage claim. Read chronology is self-report, not
independent certification.

Parent ratified 22:42:19. Fresh public HTTPS fetch, unchanged parent and full
source/direct/CLI-test visible re-anchor 22:42:26 preceded authoring.
Source blob: cd83af0b2cfd56c4db471bc352d64151e1c524f6.
Direct test blob: cdee1ba4ea013a429728936a852c447d10c54fd0.
CLI test blob: fbb50ccf96863cda4fff246dc20e5909dd0c313b.

## Exact scope

One literal call to filter_genes with
`{'genes':['g'], 'samples':['s'], 'counts':[[10]]}` and `min_samples=0`
pins exact ValueError type and `min_samples must be 1..1, got 0`.
The table passes _check; the lower-bound side of `1 <= min_samples <= n`
is false. Expected message comes from current source, not a filter oracle.
No successful return or other input is asserted.

## Author receipts, independent audit still required

Python 3.10.12, pytest 9.1.1 using existing private venv/system packages.

- New file: 1 passed in 0.10s.
- New + bio_rnaseq + CLI rnaseq: 13 passed in 0.57s.
- tests/self_improve + same three files: 1853 passed, 13 xfailed in 31.17s.
  This is not the global suite.
- Four independent temporary filter_genes-scoped mutants each fail:
  lower bound changed to 0, omitted lower bound, and return-{} guard
  raise no exception; changed diagnostic fails equality.
- Source restored byte-exact, SHA256:
  32648ec08a7385873dbf9c659209c09bc2dffee3a96e526be3e0d7c1095cf7f4.
- Restored new test rerun: 1 passed in 0.12s.

No source mutation committed. Separate audit and explicit execution or
composition instruction required before publication.
