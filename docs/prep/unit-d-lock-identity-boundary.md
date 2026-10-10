# UNIT D: lock identity and sidecar boundary

PREP-NORUN, design only. Source-derived report, not a repair or a runtime verdict.
Base prerequisite: 6e1a42145e529d50751ec3b5cedc6d6ff3105f60.
Only public source and synthetic fixtures used. No product changes proposed as
installed behavior. Test outcomes remain unknown until independent execution.

## Source anchors and path-identity matrix

state_lock.py lines 33-49 pools by str(Path(path).resolve()), once per factory
call. Each pooled object has an RLock, nesting depth and sidecar key+'.lock'
(lines 52-60). The OS lock is on the opened sidecar inode, not on JSON bytes.

| Paths/actors | Python pool | POSIX cooperation | Boundary |
| --- | --- | --- | --- |
| Same canonical path, same process and timeout | Same object/RLock | One sidecar descriptor while nested | Reentrant only on owning thread |
| Relative/absolute spelling resolving to same path | Same key | Same sidecar path | Resolution uses current working directory |
| Symlink ancestor alias stable at construction | Same resolved key | Same sidecar | State I/O still uses caller path |
| Final JSON symlink stable at construction | Same target key | Target+'.lock' | Subsequent atomic replacement may change alias relationship |
| Separate processes, same resolved path | Different Python pools | flock on same stable inode | Supported local POSIX semantics required |
| Hardlinked JSON at different names | Different keys/RLocks | Different sidecars, can both acquire | Same JSON inode is NOT lock identity |
| Ancestor/final alias changed after object construction | Old cached key | Old sidecar, unless its own ancestor changed | Caller-path I/O may now select different state |
| Canonical ancestor renamed/replaced | Same cached string | Sidecar open may select a new directory/inode | No directory pin or ancestor no-follow walk |
| Sidecar unlink/replacement while held | Same key in one pool | Holder retains old inode; new process opens new inode | Noncooperating actor breaks stable-sidecar assumption |
| fork-inherited lock object | Old pid/object | __enter__ refuses before Python RLock | Reconstruct via factory in child |
| Fresh factory call after fork | Lazy new pool/guard/pid | Closes tracked inherited descriptors, then opens sidecar | Parent still holds original open-file description |

Different timeout values for the same pooled key raise ValueError. Direct
StateLock construction is exported but does not join the shared pool; the
cooperation contract requires shared_state_lock, not manual same-key instances.

## Proposed supported-POSIX contract

This is a scoped proposed contract to review, not an authority grant:
- All participants use the shared factory and stable path spelling/alias mapping.
- The state parent directories and sidecar name/inode remain stable for all
  participants while in use. Direct editors/removers do not participate.
- fcntl.flock, O_NOFOLLOW, regular-file sidecars, reliable local filesystem lock
  semantics and writable caller-controlled directories are required. Validate
  actual deployment filesystems separately; network/distributed semantics are
  not established by reading this implementation.
- Cooperating threads serialize by the shared RLock; cooperating processes
  serialize by advisory exclusive nonblocking flock on the same sidecar inode.
- Exceptions are refusals, not success. Missing fcntl/O_NOFOLLOW raises
  StateLockUnavailable. Other open/fstat OS errors may propagate as OSError.
  There is no unlocked platform fallback. Any future alternative is a separate
  proposal requiring equivalent semantics and audit before use.
- No file-authentication, human-approval-authentication, hostile-filesystem
  containment, cross-file transaction, crash recovery or exactly-once claim.

O_NOFOLLOW protects only the final sidecar component. fstat checks regular-file
kind, not link count, owner, mode, expected inode or canonical-directory identity.
Hardlinked sidecars/JSON, alias swaps and external inode replacement are not
contained. Replacing JSON atomically is expected; its inode cannot serve as a
stable lock identity without redesigning that publication protocol.

## Timeout, fork and pool limits

The monotonic deadline begins before RLock acquisition. RLock.acquire receives
full timeout; blocked flock checks the original deadline after BlockingIOError.
resolve() in the factory, pool-guard acquisition, sidecar open/fstat, scheduler
latency and exit/unlock/close are not interrupted by this deadline. An immediate
successful flock after slow open/fstat returns even after the deadline. This is
an acquisition-contention budget, not a total operation or I/O timeout.

__enter__ checks creator pid. Fresh shared_state_lock after fork closes every
tracked _fd and replaces pool/guard/pid before resolving. It does not mutate the
old objects into reusable locks, install an at-fork handler, or clean up direct
unpooled StateLock descriptors. Closing the child's inherited reference alone
should not release a parent-held flock; this must be verified on supported OS.
Fork during an in-progress lock transition remains an unaudited boundary. Do not
call inherited __exit__ as a child cleanup mechanism.

_pool retains every resolved identity forever in a process. Released locks have
no open descriptor, but keys, objects and RLocks remain. Growth scales with
unique path identities, including alias retargeting and temporary workloads.
There is no bound, eviction or lifecycle API. Proposed resource budgeting must
include this cost; weak-pool/refcount eviction is a design option, not present.

## Gate/registry/engine scope inspected at this base

Gate and registry retain unresolved caller paths for state I/O. Gate mkdir and
registry extensions mkdir occur before lock acquisition. Their missing-file
check plus initial state save occurs under shared lock. A constructor timeout
therefore does not imply zero directory changes.

Gate _load/_save/request/decide/record use the shared lock. decision delegates to
record. coordinated_record holds the gate lock across yield and nested record.
Record is detached after snapshot; its later use alone is not coordinated.

Registry _load/_save/save_proposal/set_proposal_approval/activate/rollback and
reconcile_extensions hold locks at the appropriate body or nested load. Read
helpers use a detached _load result. dispatch reads its selected entry then
admits/executes source outside a long-held lock, later locking for counter update.
It is not serialized against all activation/rollback across its entire execution.

Engine activate does a separate initial registry read, then holds gate via
coordinated_record first and registry second across binding, commit and ledger
append. rollback uses that same nested gate -> registry order. propose and
request_rollback do sequential registry/gate calls, not one atomic transaction.
No reverse nested registry -> gate path was found in the inspected methods.
Custom gate implementations must meet the protocol; a stable identity string
alone cannot prove that they actually coordinate. Ledger locking is separate.

Existing test_state_lock_integration.py contains kind='generic' proposal fixtures;
the pinned preflight permits six kinds and rejects generic. Their apparent
lock-focused intent does not make those fixtures executable evidence. No existing
test was changed or executed; new tests focus on independent lock fixtures.

## DESIGN choices requiring later approval and audit

1. Pin a trusted directory descriptor, traverse ancestors without following
   symlinks where policy requires, and open sidecar with dir_fd and O_NOFOLLOW.
   Compare fstat inode/device against a path-at-directory stat before/after flock.
   This narrows races but does not prevent later unlink by an actor with rights.
2. Define whether aliases are refused or canonicalized once for BOTH state I/O
   and locks. Changing unresolved state paths is an API/deployment policy change.
   Keep hardlinked JSON names explicitly unsupported unless a stable separate
   lock-domain service is designed. Do not silently deduplicate JSON by inode.
3. Reserve sidecars in a protected directory with restricted mutation rights;
   make lifecycle ownership explicit. Inode comparison detects some replacements
   but cannot supply hostile-actor exclusion without trusted directory controls.
4. Choose a pool bound/lifecycle design preserving one RLock per active key.
   Naive eviction creates concurrent same-key objects; weak references need
   ownership and active-holder proofs. Do not install it as a small cleanup fix.
5. Choose explicit fork policy: disallow fork while state objects are active, or
   audited at-fork descriptor/guard reset with no unsafe inherited exit. Current
   lazy factory reset remains the observed implementation.

## Authored test contract

All tests are NOT RUN. Synthetic tmp paths only. Spawn children send READY, then
wait for GO; parent acquires and continues holding through the child's timeout or
acquisition receipt. This is not a simultaneous start-barrier contention claim.
Each child returns a typed receipt; unexpected errors are failures. Bounded
poll/join deadlines are harness watchdogs, not performance claims.

Replacement/unlink cases deliberately exercise a noncooperating actor and assert
second-inode acquisition while the original holder remains locked. That is a
limitation demonstration, not a request to treat filesystem tampering as supported.
Fork tests refuse inherited object entry and verify factory reconstruction still
contends with parent-held sidecar. Mock-clock tests advance time during open/fstat
without sleeping; they demonstrate the code's deadline scope, not real I/O speed.
Unsupported capabilities are narrowly skipped for relevant POSIX tests, while
missing-fcntl/O_NOFOLLOW fail-closed cases are explicitly authored. Skip is not PASS.
