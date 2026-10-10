# Unit C authored audit test plans

PREP-NORUN / design-only. Model test file has 11 functions / 26 proposed cases.
None run. Synthetic consistency assertions repeat design expectations; they are
not a recovery algorithm, implemented recovery contract or behavioral proof.
No existing public tests have been rerun. Published test counts in source docs
are source claims, not this packet's independently observed execution.

## Model plan and acceptance

The authored model file records six cut expectations, postreplace ambiguity,
registry_committed=None inspection alternatives, final sync failure without temp,
EEXIST version block, inactive references, six stale observation kinds, four
journal disagreement/partial cases, direct bypass, rollback and no removal grant.
A future audited recovery model must add adversarial transition generation and
state invariants; passing these static fixtures cannot establish recovery safety.

## Filesystem execution plans (not executable tests in this package)

All future runs use synthetic tempfile state, never live owner data. Independent
implementation approval and test-execution authority required. Preserve fixture
snapshots before/after with exact registry/source/consumption hashes and inode
observations; no execution of extension source. Use gate-coordinated engine path
for consumption cases, with separate direct-registry bypass cases. Reconstruct
fresh objects in a separate process, account for .lock creation as a distinct
expected effect. Do not call evidence inspection "read-only filesystem" if
object construction creates directories/state/lock sidecars.

F01: six handshaked SIGKILL cuts. Child pauses after each named checkpoint, parent
kills child only after signal, then independent fresh readback validates the full
matrix, not just bool(features). Compare exact R0/R1 JSON, source bytes, all old
active/inactive references, proposal status and C0/C1. Validate no unintended
consumption at first five cuts; committed at last. Do not label this power loss.

F02: fail atomic registry operations at open/write/file fsync/close/replace/dir
fsync. Pre-replace must show R0/C0 plus D orphan; successful replace then dir-sync
failure must show visible R1/C1 and no checkpoint, durability unknown. Read actual
bytes on registry_committed=None and simulate both stale exception/report and
external replacement. No exception alone triggers retry/adoption/removal.

F03: source failure after unlink but before final directory fsync. Assert complete
D, absent T, R0/C0. Also fail write/link/first sync and preserve partial/complete
T classifications, never adopt based on .tmp name or apparent newest timestamp.

F04: retry activation while EEXIST orphan occupies next_version. Snapshot orphan
bytes and registry/consumption, refuse overwrite/adoption/version skipping. Use
matching and mismatching orphan digests. A matching digest still grants nothing.

F05: activate multiple versions then rollback. Reconcile includes all references
including inactive. Missing/mismatched inactive file must block destructive plan.
Extra externally referenced artifact requires agreed external-reference policy;
no directory-only garbage collection assumption.

F06: noncooperating editor changes registry, sidecar, ancestor, source or journal
between inspection and decision. Test valid-looking rewrite, symlink, hardlink,
nonregular artifact and digest/generation mismatch. Recovery refuses stale plan
and preserves originals. Advisory lock is not malicious-writer containment;
self-consistent forged hashes are not authenticated evidence.

F07: journal write partial temp, pre-replace failure, postreplace sync failure,
missing/corrupt/duplicate-key/unknown-version/sequence regression. Test actual
R1 with journal INTENT, actual R0 with journal COMMITTED, simultaneous journal
and registry temps, and absent journal. Original files retained, no replay from
journal alone; authoritative inspection or HOLD.

F08: future owner-selected forward adoption under gate -> registry lock. Test
fresh matching approval, revoked/expired/mismatched approval, already consumed,
changed base digest/generation and missing candidate admission evidence. Commit
source ref + consumption in SAME JSON, preserve orphans on failure. Policy on
reusing prior approval must first be explicitly selected, not assumed in tests.

F09: quarantine/removal authorization. Without explicit grant, no move/delete.
Logical quarantine preserves bytes; physical quarantine requires its own crash
matrix and owner-selected export/retention. Changed reference set, referenced
inactive file or uncertain journal blocks removal even with an older grant.
Test partial preservation copy and postmove/presync crash without losing original
recoverability. This plan does not approve any actual removal.

F10: real power-loss assessment is separate infrastructure work. Specify supported
OS/fs/device/mount and actual reboot/storage-fault methodology, validate fsync
behavior with external measurement. Process SIGKILL, syscall monkeypatching,
assertions and model transitions cannot prove power-loss durability. Unsupported
platform or uncertain fsync contract -> unsupported/HOLD, never inferred PASS.

## Required future result receipts

Report exact implementation/source/test hashes, platform, fixture generation,
function vs case counts, collection/results/skips and every failed probe. Distinguish
model-only, injected syscall failure, actual SIGKILL, real reboot and actual
storage-power fault. Document no source execution or live data. No all-files-atomic,
exactly-once, tamperproof, approved deletion or recovered-production claim.
