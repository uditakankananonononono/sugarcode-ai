# H47 literal negative-statistic diagnostics

Parent: 2619d32b82f84588c8870c9940d319c8fc269973.
Adds only this contract and one independent test file. No product-source or
old-test edits. No successful values, math/statistical accuracy, biological
validation, or standard claim.

## Read gate and overlap

2026-10-10 IST, full gstats.py, test_bio_gstats.py and test_cli_gstats.py
visibly read at 21:47:19. Direct consumers chi_square_2x2 and genotypic_test
are in the full source. CLI gstats consumer functions/parser blocks read
21:47:25. Coverage search across tests/src/contracts found only existing
chi2_sf success fixtures and unsupported-df rejection for positive x. No
negative-x guard or exact diagnostic/precedence pin found; this is not an
exhaustive coverage claim.

Parent ratified at 21:47:37. Fresh public HTTPS fetch and visible full
source/direct/CLI tests at unchanged parent 21:47:44 preceded authoring.
This read-gate account is documentary self-report, not independent audit.
Source blob: 5d650dd90d1173a34faefe13ee2d7cdace168962.
Direct test blob: a653392153f3e90f2a7ee068ac8f78a00467f3f2.
CLI test blob: a83c6453f5ad2909dda3abb0da76d4d8145f7cd1.

## Literal scope

`chi2_sf(-1.0, df)` for literal df 1, 2, 3 pins exact ValueError type and
`chi-square statistic must be >= 0`. The df=3 case pins negative-statistic
rejection before unsupported-df rejection. Expectations are read from the
current source, not an external mathematical oracle. No other input or
successful survival-probability value is asserted.

## Author receipts, independent audit still required

Python 3.10.12, pytest 9.1.1 in the existing private venv using system packages.

- New file: 3 passed in 0.08s.
- New + bio_gstats + CLI gstats: 18 passed in 0.37s.
- tests/self_improve + same three files: 1858 passed, 13 xfailed in 30.69s.
  This is not the global suite.
- Four temporary source mutants killed: remove guard (3 failures); threshold
  changed to -1 (3 failures); guard moved after successful df dispatch
  (2 failures, df=3 still passes); changed diagnostic (3 failures).
- Byte-exact source restoration SHA256:
  0c21100325bba35b0c53263cecfaa47380105cbf8292d94154944174742a8789.
- Restored new file rerun: 3 passed in 0.12s.

No source mutation committed. Separate audit and explicit EXECUTE/composition
required before publication.
