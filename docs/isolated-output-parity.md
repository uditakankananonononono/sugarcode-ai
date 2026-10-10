# Isolated evaluator output parity

Base 6e1a421. Live containment baseline 10 cases passed before editing. Only
IsolatedRunner.run output collection changes; bwrap command/mounts/namespace/probe,
source caps, launcher CPU/RSS/regular-file rlimits, auth/dispatch unchanged.
Uses audited run_bounded_process for observed 1 MiB + 1 bytes/pipe, 4,000 BYTE rings,
overflow flag/stream/reason. Preserves isolated ACTUAL exit code on timeout, including
zero if direct child already exited and pipe-drain helper reports timeout; never
native -1 normalization. Existing SandboxResult positional shape unchanged.

Pipe-output cap replaces tempfile stream truncation, not candidate regular-file
RLIMIT_FSIZE removal. Prior RLIMIT_FSIZE already constrained child tempfile output;
this is semantic consistency + explicit overflow classification, lower severity
than native memory flood repair, NOT architecture breakthrough or unlimited-disk fix.
The 4,000-byte diagnostic tail replaces 4,000 Unicode characters. Observed bytes
are not attempted bytes; no parent total RSS/CPU guarantee or host-kernel isolation
proof. bwrap probe capture_output is trusted-config buffering, unchanged. isolated
_dispatch protocol/noise files untouched. Escape sessions/kernel/runtime trust,
pytest internal capture/disk use, exact-once host effects outside scope.

15 new cases passed; selected 1,191 = 1,176 prior + 15, no skips in this live
containment environment. Tests explicitly require real_containment fixture, not
fake pass if namespaces unavailable. Four real raw-pipe exact/one-over tests
use a TEST-ONLY subclass to add PYTEST_ADDOPTS=-s inside bwrap: avoids pytest's own
FD capture intercepting os.write. Production capture remains normal pytest mode.
Six actual generated templates pass with meaningful params (grant/filter/score,
email extraction). Ordinary failure and timeouts retain existing tests. Actual
regular-file RLIMIT_FSIZE probe passes; containment missing/failed no-fallback probe
refuses before candidate capture. No isolated RSS measurement claimed; native
historical measurement not relabeled here.

Inherited pipe note: real bwrap PID namespace tears down inherited descendants
when init exits, so original raw fork probe returned normally, not timeout. Existing
native capture real inherited-pipe test remains; isolated mapping tested with explicit
CapturedProcess(timeout=True,exit=0), NOT represented as real surviving isolated
descendant. Bwrap's stronger lifecycle behavior not weakened to force a test.
Initial 6 FAIL / 8 PASS new-test run: raw fd output hidden by pytest capture, three
empty-default template tests invalid for authored semantic samples, and inherited
namespace-lifetime expectation wrong. Fixed TEST fixtures, no production weakening.

Base selected 14 cases: 4 FAIL / 10 PASS, including two real overflow failures and
two missing capture-seam mapping assertions (not all behavioral mutation canaries).
Disabled containment refusal mutant: 1 FAIL candidate counterpart PASS. Audited
native helper cap/kill/tail mutants already stand; not counted as new isolated
mutations. Full configured suite not claimed; separate auditor required. No paid
service, no source/gate policy or PRIDICT/science changes.
