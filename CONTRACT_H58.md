# H58 literal zero-second-column rejection

Parent: 2ca81a8a88598595d44ca29e33aef325c36ad06c.
Adds only this contract and one independent test file. No product-source or
old-test edits. Pins one guard side and its diagnostic, not successful
statistics/p-values or accuracy/clinical/biological behavior.

## Documentary read gate and overlap

2026-10-10 IST: full gstats.py, test_bio_gstats.py and test_cli_gstats.py
visibly read 22:24:52; relevant allelic_test consumer is in full source.
CLI allelic/genotypic handlers and coverage searches read 22:24:59.
Existing direct rejection uses (0,0,1,1), exercising a zero row, not isolated
c2==0. H47's chi2_sf negative-statistic pin is another guard. No stronger
relevant column-guard or exact diagnostic pin found; no exhaustive coverage
claim. Chronology is documentary self-report, not independently certified.

Parent ratified 22:25:15. Fresh public HTTPS fetch, unchanged parent and full
source/direct/CLI-test visible re-anchor 22:25:22 preceded authoring.
Source blob: 5d650dd90d1173a34faefe13ee2d7cdace168962.
Direct test blob: a653392153f3e90f2a7ee068ac8f78a00467f3f2.
CLI test blob: a83c6453f5ad2909dda3abb0da76d4d8145f7cd1.

## Exact scope

One literal `chi_square_2x2(1, 0, 1, 0)` call pins exact ValueError type and
`degenerate table (zero margin)`. Current source has n=2, r1=r2=1, c1=2,
c2=0, so only the final c2==0 disjunct fires. Expectations come from current
source, not a statistical oracle. No other margin or successful result is
asserted.

## Author receipts, independent audit still required

Python 3.10.12, pytest 9.1.1 using existing private venv/system packages.

- New file: 1 passed in 0.08s.
- New + bio_gstats + CLI gstats: 16 passed in 0.32s.
- tests/self_improve + same three files: 1856 passed, 13 xfailed in 32.48s.
  This is not the global suite.
- Four independent temporary chi_square_2x2-scoped mutants each fail the
  new test: removing c2 guard side and strict c2<0 each cause division by
  zero; changed diagnostic fails equality; returning {} raises no exception.
- Source restored byte-exact, SHA256:
  0c21100325bba35b0c53263cecfaa47380105cbf8292d94154944174742a8789.
- Restored new test rerun: 1 passed in 0.12s.

No source mutation committed. Separate audit and explicit execution or
composition instruction required before publication.
