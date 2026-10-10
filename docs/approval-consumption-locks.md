# Cooperating approval consumption and state locks

Base 3d4c2cc. Approved policy: at-most-once ENGINE registry commit per canonical
gate identity + approval ID in this registry, not complete authorization or
exactly-once host effects. Legacy approval IDs and registries without consumption
metadata start unused. Direct file editors can delete metadata or restore an old
file and reopen replay. No tamper-proof or authenticated human claim.

## Commit boundary

ManualApprovalGate.coordinated_record holds the shared gate lock while yielding
canonical identity and fresh detached approval record. Engine activate/rollback
requires this interface, then acquires registry lock (gate -> registry order),
checks J05 approved binding and A01 rollback pin, and commits consumed metadata
in SAME registry JSON atomic replacement as activation/rollback state. Reusing a
consumed ID refuses, even after active-version restoration. Auto mode does not
bypass consumption. A later REJECTED decision can revoke unused approved records;
a later APPROVED decision can restore UNUSED request permission. Revoke winning
the gate lock before commit refuses; commit winning first remains effective.
No retroactive undo of committed state or external effects.

Custom gate boundary: engine.activate AND engine.rollback now require callable
coordinated_record(id) yielding (stable nonempty identity, full record) while
holding the gate's decision lock. Full-record-only custom gates fail closed.
Custom implementations are trusted injected Python, not verified or impossible
to fake. Inherited ManualApprovalGate subclasses have coordination, but exact-type
unrecorded-auto bypass remains unchanged. Generic gate request/decide/record/
decision and direct registry activate/rollback remain available, direct registry
methods are trusted effect/consumption bypass unless engine identity is supplied.

Reserved registry field engine_consumed_approvals is a SHA256-keyed map of exact
records: gate_identity,approval_id,action,feature,version,consumed_at. Every field
validated including finite nonnegative timestamp, positive exact int version,
supported engine action and identity-key consistency. Malformed present metadata
refuses complete registry read/write. ABSENT map allowed for legacy state. Missing
fields in a present record refuse. No auto repair. This field is now reserved:
an existing unrelated extension with same name no longer accepted. The map grows
within existing 16 MiB byte limit. Prospective full activation state+consumption
checked before extension write; rollback checked before JSON commit. No archival,
retention, cap increase or guaranteed future room.

## Locks

Canonical path-keyed shared RLock + stable <state path>.lock POSIX flock sidecar.
Initialization and each gate/registry load/save and read-modify-write covered.
Engine uses fixed gate then registry ordering; low-level single-resource calls
never acquire gate while holding registry. Lock is reentrant across same-thread
objects. 5 seconds total acquisition deadline for each lock, native TimeoutError
subclass on timeout. Nonregular/finalsymlink sidecars refused, unsupported POSIX
locking fails closed. New sidecar private 0600, retained (never remove while live).
Process crash releases kernel lock. After fork inherited StateLock object refuses;
new object rebuilds process-local pool/closes inherited fds. Canonical identity
follows ancestors; hardlink aliases and swapped ancestors unclosed. Sidecar can be
unlinked/replaced by hostile/noncooperating writer, advisory locking is not authority.
Blocking flock avoided, but open/fstat/regular filesystem IO itself no deadline.
Pool retained per state path, no unbounded-state-path scalability claim.

## Failure residue

Pre-replace registry failure leaves old state/unused map; activation extension can
remain orphan. Postreplace AtomicDurabilityError means BOTH consumed+state visible,
not safe to blindly retry. Logging can fail after registry commit. No cross-file
gate+registry+ledger transaction, distributed lock, consumption revocation rollback,
source generation authentication, host-effect sandbox, cross-object direct editor
containment. Low-level _save serializes replacement only, does not make external
caller stale read/edit/save transactional; use public read-modify-write methods.
Existing caps/encoding/atomic-source rules remain, no paid service or PRIDICT work.

## Executed evidence

Initial 33 new cases PASS; strengthened candidate adds 7 lock probes (40 new cases total).
Includes 4 separate two-POSIX-process cases (gate updates, registry proposals,
concurrent initialization, same-approval engine commit), start barriers are smoke checks, NOT forced overlap of all critical sections;
plus fresh Python process consumption/replay check. Six added forced contention
probes hold the parent sidecar through child timeout/result (test-only .2s), covering
gate/registry init, gate request, registry proposal, engine gate and registry commit.
Production 5s default separately asserted.
Thread races include two engine activation/rollback, two gate/registry objects,
and commit-winning vs revoke locking. Gate-ownership assertion in committing
thread avoids falsely passing because revoker transiently owns lock.

Correction of base evidence: the sole old-base PASS is
test_consumption_atomic_registry_failure_reconciles[before], pre-replace refusal
already preserved on base. Old Lock lacking _thread_lock explains the SEPARATE
revoke test FAIL, never the PASS.

Base integration canaries (new pure helper files copied for imports only, old
engine/gate/registry untouched): selected 12 cases -> 11 FAIL, 1 PASS; plus base
revoke ownership case 1 FAIL (old Lock lacks shared ownership API). These are
selected detection counts, not all 33 new cases mutation coverage. Initial whole
base new-test attempt interrupted at 45s, no completed count claimed.

Targeted mutants: disable registry consumption -> 6 FAIL / 1 PASS (pre-replace
failure case correctly passes); remove engine gate coordination -> 1 FAIL;
remove shared path-lock pool -> 2 FAIL; disable flock acquisition -> 1 FAIL.
Every targeted failing candidate counterpart PASS. An early revoke test mutant
PASSED because revoking thread could hold lock; improved deterministic committing
thread ownership assertion, reran mutant and candidate. Honest test improvement,
not hidden unsupported claim. Pure helper/process-boundary tests may pass on base
with additive helper imports, no claim all base cases fail. Initial full adjacent
2 FAIL / 1,086 PASS diagnostics/order regressions fixed preserving old assertions.
Independent fresh auditor required before any landing; local candidate not public.

Bounded audit recheck evidence: 40 new cases now PASS; selected 1,128 PASS =
1,088 prior + 40 new, no skips. Added 6 forced process probes all FAIL against
no-flock mutant, all PASS candidate, plus production 5s constant check PASS.
The earlier 4 process start-barrier cases retain smoke labels, not overclaimed
critical-section interleaving coverage. No production lock policy change.
