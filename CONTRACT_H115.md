# H115: incremental literal BED extra block size (bc1, sizes2, starts1)

Exactly two additions: this contract and
 tests/test_h115_bed_extra_size_characterization.py.
One parse_bed('chr1\t0\t9\tg\t0\t+\t0\t9\t0\t1\t4,5\t0') call pins exact
ValueError identity and 'line 1: blockCount 1 != 2 sizes / 1 starts'.
Block count 1 under-declared against 2 sizes / 1 start; count guard60,
raise61-63. SAME GUARD as H101, which pins the bc2/sizes1/starts1 mirror
literal and 'blockCount 2 != 1 sizes / 1 starts'; ordinary direct-BED regex
test (tests/test_bio_bed.py test_block_validation) covers 'blockCount 2 != 1
sizes' on a third literal. H115 is incremental exact identity/full-text on
THIS literal only (the under-declared-count direction), no generic
block-validation novelty. Source-derived pin, not an independent block-count
oracle. No other input, successful parsing, BED conformance, consumer,
model, accuracy or biology claim. No source/existing-test edits; comments
not validated.

## Read gate

Live public tip 05fc2a6040ad8a49b13077a613d1e468592ec8f9 verified
2026-10-11 00:50:27 IST before authoring; no delta vs last-reported
05fc2a60 (reservation file's b870d17 is the tip's parent). Fresh full
bed.py, test_bio_bed.py, test_cli_bed.py, H101 contract/test and H109
contract/test visibly read. Scoped H-test/contract search found the H101
same-guard overlap and the ordinary regex above; no same literal pin, not
exhaustive absence. Source blob cdaf35e536e26de74b34b8312a8cff7ab23d57e8.
Chronology is author self-report, not independent certification.

## Actual runtime

/usr/bin/python3 (3.10), pytest 9.1.1 + pluggy 1.6.0 at user site
(single ruled `python3 -m pip install --user pytest`; first ruled attempt
`python -m pip install pytest` failed exit 127, python absent), explicit
repository src PYTHONPATH, -B.
New1P/.12s. Adjacent new+test_bio_bed+test_cli_bed: 16P/.56s.
WIDER same+tests/self_improve: **38 FAILED, 1818 passed, 13 xfailed /
26.50s, exit 1 - NOT A PASS.** All 38 failures inside tests/self_improve
(test_isolated_output_parity 12, test_approval_schema_integration 12,
test_engine 5, test_sandbox_output_caps 3, test_sandbox 2, test_isolation 2,
test_strict_gap_json 1, test_mixin_wiring 1); none in BED paths; the new
test passed within the run. OBSERVATION ONLY, not a verified cause:
tracebacks show isolated/sandbox child processes exiting with "No module
named pytest"; the ruled install placed pytest in the user site, which
isolated children may not inherit. Accepted as-is under parent ruling (a);
no venv/PYTHONPATH/install corrective was permitted or taken. Selected,
not global suite; XFAILs are not implemented repairs.
Restored-adjacent after mutants: 16P/.48s.
Four independent new-only mutants on src/sugarcode/bio/bed.py, each applied
alone, each killed (1 failed, exit 1), byte-exact restore + SHA256 verify
after each:
- Count guard body return None/.20s: did not raise.
- Count guard body returns full diagnostic string/.16s: did not raise.
- Count guard raises RuntimeError/.17s: wrong type escapes.
- Count guard removed entirely/.17s: did not raise; zip(starts,sizes)
  truncates to the single fitting block (0,4), record accepted.
Final source SHA256 8f8a6cce995c76b9b16cf5d4df5ff661b96c4f0a1e6f9522627327bd8482e420
(matches pre-mutant snapshot; identical to H101's published final hash).
JUnit XML + full log per run supplied with per-receipt hashes in the
chronology manifest. No exhaustive mutant adequacy claim. No push; separate
audit/publication required.
