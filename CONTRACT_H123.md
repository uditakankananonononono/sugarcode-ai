# H123: one thirteen-field BED literal characterization

Exactly two additions: CONTRACT_H123.md and
 tests/test_h123_bed_thirteen_fields_characterization.py.
One parse_bed('chr1\t0\t9\tg\t0\t+\t0\t9\t0\t1\t9\t0\textra')
call pins exact builtin ValueError identity and full diagnostic:
`line 1: BED record has 13 fields, max 12`.
Expected class/text derived from source upper-width guard, not independent BED
oracle. First twelve fields would pass existing checks; removal ignores extra.
No other literal, conformance, successful parser, repair or biological claim.
H82/H110 lower-width pins exercise different guard. Scoped collision search
for max12/13fields/H123 in tests/contracts returned no hits at selected base;
not an exhaustive semantic coverage absence claim.

## Fresh grounding and chronology (2026-10-11 IST)

Actual start01:12:33. ls-remote/fetch found live main
579f61805f42a6c90a3769871bddc20735d401a1 (reported H122 tip).
Prior base ce6d644e was older. Full disjoint delta877 lines read before any repo
write: initial output overflow disclosed, then read ranges1-210,211-420,
421-650,651-877; no product/old-test changes, only characterization additions.
Full current bed.py/direct BED tests/CLI BED tests read; H82/H110 contracts/tests
read; BED handlers485-535 read before test writing. CLI registration1492-1518
read afterward, before mutants. This latter timing is disclosed, not retimed.
No other CLI regions or global coverage reviewed. Fresh ls-remote immediately
before writing still579f6180. New branch reanchored explicitly, no merge/rebase.

XFAIL policy search pyproject/conftest found no reported policy matches; absent
conftest paths yielded suppressed stderr, so no exhaustive policy claim. Every
run explicitly used -o xfail_strict=true; wider also --strict-markers. Existing
pytest9.1.1 environment, no installs/services/network tests/diagnostic probes.
Test written first before runs; contract authored only after actual receipts
and parent packaging ruling01:13:57. No standalone syntax/AST checks.

## Actual selected receipts

All run commands: PYTHONPATH=src python3 -B -m pytest -q.
- Named with -s, strict XFAIL:1 passed/.13s,exit0, source path/hash printed.
- Named + tests/test_bio_bed.py + tests/test_cli_bed.py:16 passed/.37s,exit0.
- Restored same adjacent selection:16 passed/.41s,exit0.
- Wider ONCE: same3files + tests/self_improve, strict XFAIL/markers:
 38 failed,1818 passed,13 xfailed/24.96s,exit1. FAILED, not global or all-green.
Raw stdout/stderr/XML retained. No baseline or root-cause claim. STOP/report
01:13:49 after wider failed; parent ruled packaging01:13:57. No rerun/diagnostics.

## Four isolated mutations

Fresh git archive of selected base into /tmp/h123-mutants-hdew062x, new test
copied there, no product file mutation in branch. Only upper-width guard altered.
Each new-only run -s prints loaded bed.py path and full source SHA256. All exit1:
returnNone DID NOT RAISE; RETURN full diagnostic STRING DID NOT RAISE;
RuntimeError same text escapes wrong class; remove ONLY len(f)>12 guard/raise
accepts record and DID NOT RAISE. Not changed-text exception in mutant2.
No exhaustive adequacy claim. Source restored byte-exactly in finally after EACH.
Original/restored/repo-unchanged SHA256:
8f8a6cce995c76b9b16cf5d4df5ff661b96c4f0a1e6f9522627327bd8482e420
Mutant full SHA256s, same order:
c6b5fde7d3f73441c311be3a2a7178f1f8c36ec783a2f665d3cf629e2992365a
4291695d32fc4b7eaae2b0406a6ecceb0bc91008ea503646e5793a2bb84e9b70
29636165c46495f4f82b91cd4d2ea6854365b2ed31635fae1cf3a5f8b49b7124
2f64341db18b992d039ce8d3e74d12efad6c7290b45f5fd4fc655d8799fc7557

One function/one case; source-hash prints are receipt evidence, no extra parser
call. No existing product/test edit, credentials/live owner state, push or merge.
Independent peer audit/landing outstanding. Wider failures remain unresolved.

## Continuation is not an audit verdict

Peer main confirmed (relayed 01:14:28): packaging continues with the wider run
recorded as FAILED 38 failed / 1818 passed / 13 xfailed, raw preserved. The count
matches the retained pattern ONLY; failure equivalence and root cause are not
verified; it neither certifies nor disqualifies. The peer's independent audit in
its own environment governs the verdict. Main's continuation ruling and the
peer's confirmation are BOTH NOT audit acceptance.
