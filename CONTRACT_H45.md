# H45 literal empty-gene diagnostics

Parent: 7c02ffbe39f2abfa04e76b38a338fe0b34d47a55.
Adds only this contract and one independent test file. No product source or
old-test edits. No success, normalization, biological accuracy, or file-format
standard claim.

## Read gate and overlap check

2026-10-10 IST: full rnaseq.py, test_bio_rnaseq.py, test_cli_rnaseq.py,
de.py and bio/__init__.py visibly read at 21:39:03-21:39:08. CLI consumer
functions and rnaseq parser blocks read; repo-wide parse_counts and diagnostic
coverage search read. Existing direct rejection tests do not exercise the
empty-gene-id branch or assert exact diagnostic row numbers. No stronger
relevant pin was found; this is not an exhaustive coverage claim.

Parent ratified at 21:39:21. Public HTTPS fetch and visible full source/direct
test re-anchor at 21:39:25; authoring blocked by missing pytest. After narrow
parent-authorized pytest provision, public re-fetch still matched the parent,
and full source/direct test reads at 21:41:19 preceded test authoring.
Source blob: cd83af0b2cfd56c4db471bc352d64151e1c524f6.
Direct test blob: cdee1ba4ea013a429728936a852c447d10c54fd0.
CLI test blob: fbb50ccf96863cda4fff246dc20e5909dd0c313b.

## Exact scope

Two literal strings:

- CSV: `\n  \ngene,s1\ng1,2\n \n   ,3\n`
- TSV: `\n  \ngene\ts1\ng1\t2\n \n   \t3\n`

Each pins exact ValueError type and `line 3: empty gene id`. Physical blank
and whitespace-only lines are removed before enumeration, and the whitespace
in the gene cell is stripped before the empty-id guard. Nonblank logical row
3 is physical row 6 here. Expectations come from current source, not an
external oracle. No additional parsing or normalization behavior is asserted.

## Author receipts, independent audit still required

Python 3.10.12; pytest 9.1.1, pluggy 1.6.0, iniconfig 2.3.1; venv uses existing
system packages. Initial missing-python/missing-pytest attempts did not run
tests and were not counted as passes.

- New file: 2 passed in 0.13s.
- New + bio_rnaseq + CLI rnaseq + bio_de + CLI de: 25 passed in 2.10s.
- tests/self_improve + same five files: 1865 passed, 13 xfailed in 31.43s.
  This is not the global suite.
- Four independent temporary source mutations each fail both new cases:
  enumeration start 1 (line 2 diagnostic); retaining whitespace-only lines
  (header rejection); skipping empty-id guard (no exception); omitting cell
  stripping (no exception). Logs and XMLs are external author receipts.
- Source restored byte-exact, SHA256
  32648ec08a7385873dbf9c659209c09bc2dffee3a96e526be3e0d7c1095cf7f4.
- Restored new test rerun: 2 passed in 0.11s.

No source mutation committed. Audit and explicit EXECUTE required before
landing; unchanged fast-forward only if this parent is still public main.
