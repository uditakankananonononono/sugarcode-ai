# H120 unrecognized first GFF attribute literal characterization

Base ce6d644e42fe596a0f760074579f3b8f35375594 verified live before writing by
ls-remote and fetch at 2026-10-11 00:54:43 IST. No delta from reported tip.
Exactly two additions: this contract and
`tests/test_h120_gff_unrecognized_bad_characterization.py`.

One direct parse_gff('chr1\ta\tgene\t1\t9\t.\t+\t.\tbad') call pins exact
builtin ValueError identity and full text:
`line 1: unrecognized attribute syntax 'bad'`.
No parser modification, no new capability, no exhaustive coverage claim.
Existing test_bio_gff already regex-checks this branch with first attribute IDg
and newline; same branch/different literal. H95 second-item ID=g;bad instead
selects GFF3 and rejects malformed GFF3 syntax. H96/H107 GTF errors differ.
Scoped collision search found no H120 path or same full literal diagnostic;
this is a bounded search finding, not global novelty proof.

Full gff.py, direct GFF tests, CLI GFF tests, H95 and H113 tests read before
writing; CLI GFF handlers and pyproject read separately. Scoped rg over H*
tests/contracts and CLI produced a head-limited 100-line initial overview;
this truncation is a read gap, not exhaustive review. Separate exact full-text
and H120 searches returned no hits. No unrelated source sweep claimed.

pytest import probe failed ModuleNotFoundError. One permitted
python3 -m pip install --user pytest succeeded (pytest9.1.1, iniconfig2.3.1,
pluggy1.6.0; other requirements already installed). No retries/broader install.
python3 used instead of literal python; main explicitly approved this substitution
at 00:55:36 IST after initial runs had already used it. No alias/symlink.
Tests authored first at 00:55:01 IST, before this contract.

Receipts, commands all use PYTHONPATH=src python3 -B -m pytest -q:
- named test, --junitxml=/downloads/h120-named.xml: 1 passed, exit0, .09s.
- named + tests/test_bio_gff.py + tests/test_cli_gff.py:17 passed, exit0,.52s.
- restored same adjacent selection:17 passed, exit0,.33s.
- wider ONCE, same3files + tests/self_improve, --strict-markers
  -o xfail_strict=true:38 failed,1819 passed,13 xfailed,exit1,21.43s.
  1870 cases,zero collection errors. All raw failures retained. No global-suite
  or wider PASS claim. No further dependency installs or failing-path repair.

Four independent _parse_attributes mutants, each restored byte-exactly in finally:
1. return None: TypeError unpacking None, test FAIL exit1.
2. return ('gtf',{}): accepted record, DID NOT RAISE, test FAIL exit1.
3. RuntimeError: wrong exception identity, test FAIL exit1.
4. remove unrecognized guard: ValueError identity passes, malformed GTF diagnostic
   fails full-text assertion, test FAIL exit1.
Each changes only gff.py temporarily; no mutant committed. -B avoids newly
writing bytecode. Raw script logs include full mutation SHA256s and timestamps.
Original/restored gff.py SHA256:
c3650708b855eb251c45fbcf8511a1b0e154295eb2b8eac622f952440f859feb
Mutant SHA256s in order:
e693f05937063cbe5f941b2f2ed900d4483fe7ff59aab8048ea12e535991bce0
77c0e4e7ced417478b942d3407c4bdc47a9df348e0d9e28be4517168c8d21e8e
a5e6a853a7673f973d0485fec17934bc5870f401673cf69db5cc8f51c92e09d6
a06fb952c93ac1bd70a23988c228f395747386cc22383c459928230f2b5c3d82
cmp and sha256sum confirm restore. No credentials/live owner state/network tests,
pushes or main writes. Peer independent audit/landing outstanding.
