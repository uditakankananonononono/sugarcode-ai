# H54 one literal K80 x==0 return

Parent: bc00975e3a33d7a0db7f3a1177e7c638ac256c8c.
Adds only this contract and one independent test file. No product-source or
old-test edits. Current-code return-value pin only; no mathematical-model
accuracy or evolutionary/biological claim. No JC69 or y-guard coverage claim.

## Documentary read gate and overlap

2026-10-10 IST, full phylo.py, test_bio_phylo.py and test_cli_phylo_trees.py
visibly read at 22:13:53. Relevant helper _site_counts and consumers are in
full source. CLI dist/build/cophenetic handlers and parser blocks read at
22:14:03. Coverage search across tests/contracts found successful K80 values
and tree composition, not a K80 saturation-return pin. Existing JC69
saturation test is a different branch. No exhaustive coverage claim.

Parent ratified at 22:14:06. Fresh public HTTPS fetch, unchanged parent and
visible full source/direct/CLI-test re-anchor at 22:14:13 preceded authoring.
Read chronology is documentary self-report, not independently certified.
Source blob: 5494887d00214e3b8f312ab2464922ab1d47797d.
Direct test blob: 8a62b2f092214165bbf202b3da1aeba06a2d53dc.
CLI test blob: e0831d75024f051f0728919175941d3ff40a2001.

## Exact scope

One literal `k80_distance("AA", "AG") == math.inf` assertion. Current
source counts two comparable columns and one transition, giving p=0.5,
q=0, x=0, y=1, so the x<=0 side returns math.inf. Expected value is derived
from current source, not an external model oracle. No other input or
successful finite distance is asserted; y<=0 is not exercised by this fixture.

## Author receipts, independent audit still required

Python 3.10.12, pytest 9.1.1 using existing private venv/system packages.

- New file: 1 passed in 0.09s.
- New + bio_phylo + CLI phylo_trees: 15 passed in 0.57s.
- tests/self_improve + same three files: 1855 passed, 13 xfailed in 30.52s.
  This is not the global suite.
- Four independent temporary source mutants each fail the new assertion:
  strict x<0 guard and dropped x guard each reach math domain error;
  return-zero mutant returns 0.0; transversion numerator mutant returns -0.0.
- Byte-exact source restoration SHA256:
  0a5c47e67621a0c7ad552b1e5390cdb857304725cea08b9c2a55579750dcacc5.
- Restored new test rerun: 1 passed in 0.11s.

No source mutation committed. Separate audit and explicit execution or
composition instruction required before publication.
