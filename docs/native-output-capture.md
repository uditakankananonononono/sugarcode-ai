# Native bounded stdout/stderr

Base 521881d. Native POSIX SandboxRunner only. Each pipe admits 1 MiB physical
bytes plus one refusal byte, via selector/nonblocking reads. Keeps 4,000 BYTE
ring per stream, replaces invalid UTF8 when returning diagnostics. Deliberate
behavior change from prior 4,000 Unicode-character tail. Ring storage max 8,000
bytes combined; chunk up to 64 KiB, transient extend up to twice ring length.
Not exact RSS cap, complete attempted-output count or child-memory prevention.

Overflow returns passed=False, output_limit_exceeded=True and named stream plus
reason. Two fields appended AFTER workdir, old positional SandboxResult construction
unchanged (IsolatedRunner unchanged). Timeout still timed_out=True/exit_code=-1,
reason and bounded stdout retained. Engine evaluation logs additive output fields.
Success/nonzero exit ordinary behavior unchanged. Native workspace cleaned in finally
unless keep_workdirs requested. Launch positive-finite timeout validates in capture
helper; source admission remains before launch. Deadline covers pipe lifetime even
when direct child exits and descendant inherits descriptors. Kill process group
with SIGKILL then reap direct child on overflow/timeout/unexpected read exception;
descendants may briefly remain dying/zombie, not live executing indefinitely in
the same group. Test waits bounded status convergence after signal, not launch race.

OUT OF SCOPE: IsolatedRunner disk-output, isolated_dispatch result/noise files,
pytest intermediate capture/disk storage, setsid-escaped descendants, host effects,
CPU/RSS quota, kernel/slow system IO, exactly-once side effects. In-process/native
candidate can perform arbitrary effects; this does not contain them or undo them.

23 new cases PASS, selected 1,151 PASS = 1,128 prior + 23, no skips. Actual Python
os.write infinite floods observed exactly 1,048,577 bytes on flooded stream then
killed; retained ring <=4,000 per stream. Exact edge, both pipes, short read,
nonzero/empty, invalidUTF8, inherited pipe after parent exits, direct child read
failure kill/reap, descendant timeout kill, real pytest flood and engine flags,
keepdir/timeout and unchanged positional fields covered. Initial instrumentation
counted Popen's internal error pipe and was fixed to own stdout/stderr only.
One descendant status assertion initially raced signal delivery; bounded kernel
status convergence now asserted. No arbitrary deterministic signal scheduling claim.

Measured /proc RSS environment only, separate harness: baseline 17,744 KiB,
peak 18,120 KiB, 10 samples, observed 1,048,577 bytes, retained peak 4,000 bytes,
stdout overflow, child exit -9. Delta 376 KiB is measured, NOT universal guarantee.
Instrumentation + bounded allocation code establish capture storage, not total RSS.

Base real-wiring probes 4 FAIL (old fields/cap absent), candidate 4 PASS. Reusable
helper did not exist on base, no claim all 23 base probes fail. Mutants: disable
cap -> 2 FAIL / 2 exact-edge PASS; disable ring trim -> 1 FAIL; disable overflow
flag -> 1 FAIL. disable group kill -> 1 FAIL (finite child, no unbounded hanging mutant);
real read-failure child reap and same-group timeout probes run. Separate auditor
before landing, no full configured-suite claim. No paid service or PRIDICT changes.
