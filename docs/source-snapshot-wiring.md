# Production source admission and snapshot consumption

Parent-approved policy2026-10-10, base84eed10. Fixed production ceilings1MiB UTF8
code/1MiB test source. Proposed-only helper contract now superseded for THESE
caller paths; pure helper still accepts explicit limits. Same byte policy across
proposal, synthesize/evaluate, sandbox/isolation writes, activation and dispatch.
No paid service or science/PRIDICT change.

R01 preflight admits code/test in bounded encoding chunks before filesystem writes.
Engine synthesize refuses before candidate registration/hash properties, evaluate
before even injected custom evaluator. Both native runners admit before workspace
creation and write accepted bytes rather than re-encode source. Large input strings
were already allocated, no pre-generation memory/CPU bound or rollback of that use.

Activation reads one regular-file descriptor with cap/hash/UTF8 admission; writes
exact verified snapshot bytes to extension, no copyfile reread. Dispatch still runs
IN PROCESS (no new isolation guarantee): importlib creates module/spec metadata,
but execution compiles verified snapshot bytes and execs namespace, never loader
source/pyc reread. Preserves __file__/module name/normal imports; no pycache loaded
or generated through this execution route. isolated_dispatch likewise stages the
same verified bytes after bounded source read, preexisting containment unchanged.

DELIBERATE behavior changes: over1MiB code or tests refuse, final symlink/nonregular
source files refuse; activation now hashes RAW original UTF8 bytes instead of
universal-newline-normalized text. CRLF code now works consistently with raw
proposal checksum and is preserved at activation. Existing LF sources unchanged.
UTF8 only remains; BOM retained. Invalid code digest/encoding/regular-file admission
maps RegistryError with native cause in activation/dispatch; proposal byte limit
InputLimitExceeded(ValueError), native runners/engine admission ValueError/native
encoding errors. No universal error normalization. Existing tamper diagnostics
retained to preserve caller match expectations. Pure helper exception types remain.

Limits: hashes describe bytes read, not immutable generation/authorship/consent.
No cross-process/ancestor path authority, external writer snapshot isolation,
symlink races during _contained resolution, disk write crash/atomic extension-file
transaction, registry+file cross-commit guarantee, approval consumption/revoke closure.
Snapshot avoids reload after read; can still read concurrently mixed bytes that
happen to match supplied digest. In-process code can do arbitrary host effects,
imports or own IO; compile/execute CPU/RSS/item budgets not provided. Slow regular
filesystem IO can block despite FIFO admission protection.1MiB is engineering
limit, not real-usage capacity proof. Future helper edits must preserve shared caps.

22new actual wiring cases cover1MiB exact/oneover, proposal code/test preIO, real
CRLF activation/digest/dispatch, activation/dispatch/isolated oversized/symlink/FIFO
refusal unchanged registry, native runners before workspace, custom evaluator
refusal, path replacement after admission NOT reloaded, invalidUTF8/surrogates.
Existing self-improve/shared/router selection run with exact denominator in packet.
Initial1058selection had2FAIL/1056PASS due changed diagnostic wording; restored
integrity/changed-since-proposal messages, no old assertion weakened. Independent
verdict before landing. Historical helper remained unwired at its own landing;
that old claim is corrected by this distinct production unit, not retroactively.
