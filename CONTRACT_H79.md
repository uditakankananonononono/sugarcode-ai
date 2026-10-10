# H79: log-odds empty literal equality

Runtime-characterized, awaiting independent audit and publication decision.
Two additions only, no production changes.

Base98f3f835b322fc60f60b0470ba9d92a8a72b25a9 confirmed live before authoring.
Fresh full pwm.py63 lines read; blobfc5fb45063b2f3019cb9dd184c195e2a6e3a749a.
log_odds_matrix defined27, comprehension28. Literal probe returns[].
Full direct/adjacent reads: bio-utils60, bio-motif87, P05 12, H76 test.
Consumer context: motif1-120, splice1-110. Consumer provenance in comments
is not independently validated by this characterization.
Direct-name collision search found nonempty utils call, no direct empty pin;
H76 build_pwm rejection and P05 normalized_score input are different APIs.
This scoped search does not establish exhaustive coverage absence.
Parent assigned H79 and ratified the read-only proposal before authoring.

Test directly imports log_odds_matrix, one call and one assertion:
log_odds_matrix([]) == []. No output-type identity assertion, no general input,
log arithmetic, background, floor, BASES, scoring, consumer or biology claim.
Outer comprehension performs zero iterations. Equality is not a validated
log-odds model, matrix contract or scientific accuracy claim.

## Author runtime receipts

Interpreter /tmp/sugar-build-venv/bin/python, explicit repository src PYTHONPATH.
New1 passed/.13s.
Adjacent new+tests/test_bio_utils.py+tests/test_bio_motif.py+
tests/test_p05_pwm_normalized_score_unknown_base.py:18 passed/.33s.
Wider selected same+tests/self_improve:1858 passed/13 xfailed/35.61s.
Not an entire configured-suite run; XFAILs are not repairs.
Restored new1 passed/.14s.

Independent new-only mutants, source restored between each:
- return None:1 failed/.15s.
- return {}:1 failed/.15s.
- return [{}]:1 failed/.17s.
- unconditional ValueError:1 failed/.17s.

Named survivors, each1 passed/.14s:
- Default background changed0.25 to0.5.
- Log floor changed1e-9 to1e-3.
- BASES changed ACGT to A.
No iterations means these do not affect this input; no claims about them.

Source restored byte-exact, final SHA256:
5c227a131dbdbfcc6b95a66daa7aeb2327c3c1c7a268e8207b83b02a7c6d6b5c.
Separate XML receipts and full mutant log accompany read-only package.
No push; publication requires separate instruction after independent verdict.
