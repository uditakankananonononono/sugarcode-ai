# Single-file gate and registry atomic replacement

Base35998c7. Peer PREP commit2c64325 supplied helper and23 authored tests, not
verification. Peer later clarified py_compile occurred despite initial "nothing
run" wording. Local builder actually ran all cases and integrated gate/registry.

Gate initialized '{}' and _save finished validated JSON string now use same-dir
exclusive temp, write loop, file fsync, close, os.replace, directory fsync.
Registry _save uses finished existing json.dumps string and same helper, including
initial creation. Registry JSON semantic/strict-write policy is UNCHANGED.
Gate snapshot/InvalidApprovalState/depth/10,000-total-history behavior preserved.

New targets default0600; existing mode preserved using fchmod before writing,
not os.open alone (which applies umask). Ownership, ACLs and xattrs are not copied.
Explicit mode argument remains subject to umask for new targets. Symlink/nonregular
observed targets refused. Parent directory must exist. Strict UTF-8 encode first.

Pre-replace write/sync/close/replace failure leaves prior target content complete;
cleanup attempted, cleanup failure may leave temp but original error preserved.
After successful replace, directory-sync failure raises AtomicDurabilityError
(replaced=True): NEW state is already present, so do not treat exception as
"nothing happened" or blindly retry. Callers currently propagate this error;
read actual state to reconcile. No automatic operation replay.

Scope: Linux/POSIX local filesystem tested, conditional on normal rename/fsync
semantics and no hostile concurrent filesystem mutation. Windows/unavailable
O_DIRECTORY directory fsync skipped; preservation via fchmod requires supported
platform. No cross-process lock, symlink-race security boundary, compare-and-swap,
cross-file transaction, lost-update prevention, exactly-once or complete operation-
plus-ledger guarantee. Hard crash can leave temps. Startup exists-check races
remain; do not run concurrent initializers. OS/filesystem durability not proven
by injected failure tests. No live approval authority added.

Tests verify helper old/new contents, private mode, injected open/write/fsync/
close/replace failures, short writes, symlinks, encoding, cleanup, postreplace
error and gate/registry actual save/init wiring. Independent verdict required.

## Independent findings and amendment

Independent reviewer reproduced34 atomic cases and232 selected cases on POSIX.
Code verified, peer lineage not independently established from archive contents;
retained git parent is builder evidence, not reviewer lineage authentication.

ORPHAN-ID correction: gate.request catches postreplacement AtomicDurabilityError
and adds .approval_id, the exact persisted newly generated request ID, then rethrows.
Caller must inspect replaced=True and this ID, read the stored request and reconcile;
do not blindly retry. This does NOT return normal success or suppress durability
failure. Other operations keep propagating state-already-replaced uncertainty.
Pre-replacement failures have no persisted request ID guarantee.

Hardlink behavior: atomic replacement breaks that directory entry's hardlink
association. Other names linked to the old inode retain OLD content. Do not use
hardlinked state as a mirrored/live-update mechanism. Existing ownership/ACL/xattr
not retained. Original prep test marker corrected to note actual local execution.

Independent amendment verdict relayed2026-10-10: VERIFIED exact orphan-ID fix,
hardlink note and test provenance correction. Real filesystem request probe
confirmed persisted ID exposure; successive failed requests create distinct IDs,
so explicit reconciliation still required. Constructor also replaces '{}' and
can raise postreplacement durability failure WITHOUT approval_id: file may exist
though construction failed; inspect actual state before repeating construction.
Decide durability and auto_approve branches were not re-probed in amendment
review (earlier decide case is builder evidence); do not inflate its scope.
