# H27 test-only descendant terminal observation (authored NOT RUN)

Parent a29dddd5095822d6aa8504c0e3602ecbe7aaf337. Product bounded_process.py
unchanged, direct-child wait/kill contract unchanged. No PID/name validation added.
Test helper belongs ONLY under tests, not shipped API. Test-first authored
fake cases, then existing descendant assertion uses single-snapshot poll.

One read per poll, FileNotFoundError=absent, parse State once, one monotonic2s
deadline unchanged, last-state/elapsed samples returned for assertion diagnostics,
no final independent read. Z/X mean terminal/nonexecuting for THIS descendant
test, not proof of reap/disappearance. Live states fail. Existing .01 polling
cadence retained and bounded by remaining time; no arbitrary exit sleep added.

Counterpart evidence, not reproduced/read original receipt: peer's first wider
run sc-h25-domain.xml failed test_same_group_descendant_killed_on_timeout at95;
final /proc/57965/status showed python, State X(dead), PID/TGID57965, PPid1,
TracerPid0. Single final snapshot, X duration unknown. No elapsed trace and no
root-cause or continuous-X claim. Exit/reap timing remains a hypothesis.

Peer-fetched references, not read by builder:
https://man7.org/linux/man-pages/man5/proc_pid_status.5.html
proc_pid_status(5) lists R/S/D/T/t/Z/X, X=dead. Enumeration is NOT duration proof.
procps(1) "dead (should never be seen)" is another ps surface, NOT /proc authority.
wait(2), counterpart report: orphaned zombies adopted by init/subreaper and
reaped, no timing guarantee; discusses zombies, NOT continuous X. No independently
observed wait(2) URL supplied, none fabricated. PPid1 consistent with adoption,
not complete timing/reaping proof. Product guarantees direct child reaping only.

Read depth at exact parent: bounded_process.py1-103 blob01514bab1262740e865a1ff8835d72841e588deb;
test_bounded_process.py1-120 blob942c4611d1ad5ab49e6522f70ef342ec603049a7;
test_bounded_process_pipe_cleanup.py1-89 blob5d256ad349669fc93836773bf1b4e006ea94722c.
All full files re-read at parent; unchanged from historical9a6b9380. Bundle hash
0c0d1b30807d8f9a9ace028035f14b4e2e3620c641c86a380ce3a5e0c1c4effb matched;
local git tip verified. No network needed.

RUN: git/text/hash operations only. NOT RUN: syntax/AST/compile, imports/product,
processes, tests/pytest, network/pip. Peer owns deterministic tests, repeated real
process canaries and mutants; no PASS/root-cause/exhaustive-mutation claim here.

Final relayed clarification supersedes earlier "no PID/name validation" wording:
expected PID marker and expected/observed Name are diagnostics ONLY when available,
not terminal predicate, PID reuse proof or authorization. Unknown/malformed states
and non-absence read OSError return failed observation with error/last-state/elapsed
samples; no silent pass. FileNotFoundError alone means absent. Additional fake
unknown/identity-diagnostic cases authored, NOT RUN. Expected executable filename
is diagnostic only and kernel Name truncation/different labels do not prove identity.
