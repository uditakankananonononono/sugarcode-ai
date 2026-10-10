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
