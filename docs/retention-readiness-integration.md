# H01 protocol readiness, not retention completion

Base2aefa5a. Parent2026-10-10 approved pure protocol + fail-closed current policy
wrapper ONLY. No live adapter or archive publication. Eligible set EMPTY without
explicit cold-history role grant. Caller-supplied cold_history in low-level pure
helper remains unverified input; J05 is a record schema, NOT a trusted classifier.
The pure helper can model a partition, not authorize or perform one.

prepare_current_policy_plan refuses every nonempty selected ID, labels all state
unknown, preserves full active state with no shards or fails capacity. Terminal
status, old timestamp and capacity pressure never establish an exception. Returns
bytes only, no gate/state mutation, storage service, metadata migration or deletion.
No attempt at immutable local snapshot storage, that is a separate unapproved design.

47peer helper cases actually PASS;6actual policy wrapper cases PASS;363selection
(310baseline+47peer+6wrapper), no skips. Pure crash cut model tests are not real
process/filesystem durability evidence. Parent policy wrapper is not authentication
or an unforgeable grant; low-level helper remains publicly callable pure model.

Readiness prepared. Full H01 blocked on explicit eligible IDs/classification grant,
headroom and capacity contract (including real indented gate bytes and expected
payload/decision growth), archive storage/retrieval identity, shared locking,
generation checks, commit/recovery design and tests. No live movement/removal.
An eventual removal from active state needs its OWN explicit decision. Until then
history ceiling may still block all gate requests/decisions; this helper does not
fix it or permit losing facts to make space. F02 caps likewise finite and not
usage-proven. No automatic age/status sweeps, retention, TTL, purge or cap increase.

Historical PREP doc says gate write_text not atomic, stale after landed F01:
current gate uses atomic_write_text single-file POSIX semantics. That does NOT
supply archive/index cross-file transaction or crash recovery. It also says J05
must supply classifications, incorrect: no such trusted classification exists.
Remaining PREP ownership/instructions are design history, not authority.
Independent verdict before any source landing, which would still be readiness
only. All code additive, live production paths untouched.

Independent VERIFIED pure model + empty-policy wrapper363PASS reproduced, NOT
archival/retention/ceiling relief. Low-level pending guard matches exact "pending"
only; case/whitespace/missing status can model movement if caller asserts cold role.
Wrapper blocks ALL selections today. Manifest roles self-asserted, hashes consistency
not authorship. No storage/locking/recovery/capacity evidence, no mutation testing.
