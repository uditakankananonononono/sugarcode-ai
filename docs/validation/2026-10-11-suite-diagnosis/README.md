# SugarCode suite diagnosis - 2026-10-11

Tested commit: `a9b532dedb7ab825a7c21ffb220b4bb324f42bde`.

## Verdict

All 58 inventory failures are environment-caused in this failure set. The exact 58 nodes fail under a controlled missing-RNA/system-child-interpreter setup and pass unchanged in the existing Python 3.10 venv. This demonstrates no product-code defect for these failures. It does not certify the product beyond these tests or remove the environment/preflight weakness.

- 20 failures: ViennaRNA's `RNA` module unavailable.
- 38 failures: sandbox children cannot import pytest. Parent user-site pytest does not remain available after HOME/environment scrubbing or `-I` isolation.
- The 16 IndexErrors are downstream empty proposal lists, not independently demonstrated engine defects. Other assertions about timeout, output caps and valid candidates also fail before their intended behavior runs.

## Current full configured suite

Five disjoint processes: 5,551 passed, 14 skipped, 13 xfailed, 0 failed. Collected 5,572 runnable cases. Skip receipts include six collection-level module skips and eight runtime skips; they are not all collected cases. No `*_test.py` files were omitted. Configured testpaths include tests/ plus six PG guideline cases outside tests/.

| Run | Passed | Skipped | Xfailed | Seconds |
|---|---:|---:|---:|---:|
| self_improve | 1840 | 0 | 13 | 42.18 |
| batch0 | 784 | 6 | 0 | 17.39 |
| batch1 | 1029 | 2 | 0 | 42.10 |
| batch2 | 891 | 4 | 0 | 34.38 |
| batch3 | 1007 | 2 | 0 | 56.73 |

Command shape: `PYTHONPATH=$PWD/src /tmp/sugar-build-venv/bin/python -m pytest -q -p no:cacheprovider <disjoint paths> --junitxml=<receipt>`.
The initial monolithic attempt timed out and is incomplete; it is not the basis of the passing total.

## Exact paired reproduction

The controlled experiment changed no repository code. Its harness set `sys.executable=/usr/bin/python3` for subprocesses and used an import hook to make RNA unavailable. Result: 58 failed in 3.46 seconds. This is a causal experiment, not a byte-identical reproduction of the inventory environment. The same 58 nodes with the normal venv interpreter and installed ViennaRNA pass in 14.00 seconds.

A direct engine probe using the same candidate shows missing child pytest, tests_passed=false and proposals=[] with the system child; the venv child passes its five synthesized tests and produces one proposal. This connects the empty-list IndexErrors to the import failure.

An earlier broad altered-interpreter probe timed out and produced extra unrelated subprocess errors. Its total is intentionally excluded from conclusions.

## Count reconciliation

The 2,270 header entered STATUS.md at October 7 commit `d20e807ecd0b193d48f906a4f9692d5e550a0372`. It was historical, not a current test count. The same document later reports 2,735 for October 9. Tests/ collection grew from 2,286 at that October 7 commit to 5,566 at the diagnosed commit, an increase of 3,280 collected cases under this venv; 248 test/PG files changed, with 48,273 inserted lines and 16 deleted lines. The stale date and test growth account for the major discrepancy, not a sudden increase in passing behavior.

Inventory selected tests/ only: 5,488 pass, 58 fail, 11 skip, 13 xfail. Six configured PG tests were outside its selection. Our current venv passes 5,545 tests/ cases plus the six PG cases. The one-pass difference from the inventory's 5,546 pass-or-fail cases and the skip differences are not exactly reconciled: optional packages differ and module-level skips hide whole files. This run lacks Bio, rdkit, primer3, pydeseq2 and some optional splice dependencies; the inventory had several of them. Neither pass total should be substituted as a like-for-like result without its environment.

At the exact October 7 commit this venv rerun yields 2,278 passed / 14 skipped, versus the old reported 2,270 / 16. That historical difference remains unresolved. It is not silently corrected or attributed to a guessed dependency.

## Action

Correct the stale STATUS header with dated current receipts. Separately track an explicit child-interpreter dependency preflight and environment error propagation for both sandbox runners. No runtime code change is part of this diagnosis.

## Receipts

`per-failure.csv` gives all 58 node-level verdicts, controlled failures, unchanged passes and error messages. `receipt.json` records counts and SHA-256 hashes of the raw XML/log receipts. Diagnostic attachments contain logs, XML, collection lists, interpreter probes and the environment freeze.

Source: checked-out repository, git history, original inventory log and locally executed pytest/XML receipts. Repository URL observed during validation: https://github.com/uditakankananonononono/sugarcode-ai/commit/a9b532dedb7ab825a7c21ffb220b4bb324f42bde
