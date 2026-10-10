# H116: literal BED extra-start characterization

PREP-NORUN. Authored test only, not runtime-characterized, tested or repaired.
Exactly two additions: CONTRACT_H116.md and
 tests/test_h116_bed_extra_start_characterization.py.
Prerequisite: 05fc2a6040ad8a49b13077a613d1e468592ec8f9, public main rechecked
immediately before writing. No anchor delta from reported 05fc2a60.

One literal: parse_bed('chr1\t0\t9\tg\t0\t+\t0\t9\t0\t1\t9\t0,1').
Expected exact builtin ValueError identity and full diagnostic:
'line 1: blockCount 1 != 1 sizes / 2 starts'. One authored test/function/case.

Full reads before writing: src/sugarcode/bio/bed.py, tests/test_bio_bed.py,
tests/test_cli_bed.py, CONTRACT_H101.md and H101 characterization test.
Current source lines 55-57 parse bc=1, sizes=[9], starts=[0,1]. Guard line 60
checks bc == len(sizes) == len(starts); first equality passes, second fails.
Lines 61-63 construct the expected diagnostic. This is source-derived reasoning,
NOT an observed probe or independent BED oracle.

Collision search: exact expected diagnostic, 0,1 and count/H116/extra-start
terms over tests/*bed* and CONTRACT* at this base. No exact H116 pin found in
those searched paths; no exhaustive absence claim. Ordinary test_bio_bed.py
lines 31-33 already exercises this same guard with a regex on another literal.
H101 pins bc2/sizes1/starts1, same guard and identity/text shape. H115 reservation
pins bc1/sizes2/starts1, same guard, but is not published at this base. H116 is
incremental extra-start literal coverage only, not generic validation novelty.

Dependency action: single python -m pip install pytest attempt at 00:50:22 IST
2026-10-11 failed exit 127, python: command not found. Parent ratified fallback
PREP-NORUN. No retry, --user or other install. No tests, imports, direct calls,
syntax checks, probes, mutations, restore executions or PASS counts. No product,
existing-test or other file edits, pushes or merges. Peer execution and verdict
remain outstanding; tests-first execution was blocked before authoring.

Peer planned commands, NOT RUN by builder, in disposable independent worktree:

    PYTHONPATH=src python -B -m pytest -q tests/test_h116_bed_extra_start_characterization.py
    PYTHONPATH=src python -B -m pytest -q tests/test_h116_bed_extra_start_characterization.py tests/test_bio_bed.py tests/test_cli_bed.py
    PYTHONPATH=src python -B -m pytest -q tests/test_h116_bed_extra_start_characterization.py tests/test_bio_bed.py tests/test_cli_bed.py tests/self_improve

Wider is this scoped selection only, not global. Record actual counts and strict
XFAIL handling; existing XFAILs do not become implemented repairs.
Isolated one-at-time mutations only: count-guard return None; return full
expected diagnostic string; raise RuntimeError; remove count guard. For the
last, source inference says zip(starts,sizes) considers only fitting (0,9),
so accepted record should violate this test. Expected failures are NOT observed
mutant evidence. Peer must require exit 1 and failure cause, byte-exact original
restoration with SHA256 after EACH mutant, then restored adjacent selection.
No other mechanism authorized. Stop on missing dependency or mismatch.

No successful parser, consumer/biology, broad schema/count-policy, clinical,
repair, exhaustive mutant adequacy or full-suite claim. One literal only.

## Later environment ruling and actual execution, separate new commit

The PREP-NORUN statement above records the initial chronology, not final state.
Parent's later explicit one-action ruling allowed python3 -m pip install --user
pytest. That single action succeeded (pytest9.1.1, pluggy1.6.0,
iniconfig2.3.1 user site). Required final pip show and pluggy import both exit0.
No retry, uninstall or broad corrective install. python3 was used because the
initial python command was absent; substitution reported before test execution.

Actual separate selections:
- New-only: exit0, 1 passed in0.10s.
- New plus test_bio_bed.py and test_cli_bed.py: exit0,16 passed in0.72s.
- Same plus tests/self_improve with -o xfail_strict=true: exit1,38 failed,
  1818 passed,13 xfailed in25.73s. Scoped selection, NOT global or all-green.

STOP on mismatch/dependency gap. Observed isolated runner stderr contains
'/usr/bin/python3: No module named pytest'. Outer user-site python3 can run
pytest but isolation does not use that environment. Empty engine proposal
failures also occurred; not all causes individually diagnosed. No corrective
install or rerun. Mutants and restored-adjacent remain UNRUN. Product bed.py
was never edited; no byte-restoration execution or mutant adequacy claim.
One literal's new/adjacent results do not establish generic BED repair. Exact
command chronology and raw stdout/stderr are delivered outside this two-path
commit. No syntax checks performed at any stage.

## Explicit continuation after STOP disclosure

Parent directed continuation after wider disclosure. In isolated temporary
archive workspace only, four one-at-time guard mutations each exited1:
returnNone 1 failed/0.11s; return full diagnostic 1 failed/0.12s;
RuntimeError 1 failed/0.13s; remove count guard 1 failed/0.11s. First, second
and fourth failed DID NOT RAISE ValueError; third exposed RuntimeError with the
expected diagnostic. No collection/import failure counted as mutant evidence.
Byte-exact original bed.py restored after EACH, SHA256
8f8a6cce995c76b9b16cf5d4df5ff661b96c4f0a1e6f9522627327bd8482e420.
Restored-adjacent exit0,16 passed/0.40s. Original branch product file unchanged.
Driver source, commands, exact timestamp log and raw output delivered. No
exhaustive mutant claim. Wider remains FAILED, no inherited/full-suite green.
