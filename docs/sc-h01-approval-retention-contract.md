# SC-H01 approval-history lifecycle proposal

Status: PREP ONLY. Tests authored, not run. No gate integration or repair claim.
Base verified in fresh public clone: 35998c7efc977a4682abb5e2e410d62ee4a4e3fd.
Source: https://github.com/uditakankananonononono/sugarcode-ai

## Existing boundary and scope

SC-J04 gate.py snapshots the complete prospective state through snapshot_json,
which counts expanded values including the root and containers, rejects depth
above 64, and caps values at 10,000. Growing history can block both new requests
and decisions. Its write_text is not atomic. This proposal does not change that
code, the approval reader, the JSON write boundary or any production path.

Added standalone approval_retention_plan.py performs a pure, bounded partition
and whole-source replay. No disk/network IO, clock, policy inference, gate
imports, state mutation, authority validation, schema migration or deletion.
The helper's interfaces below are a written proposal, NOT an existing shared
SC-J05 API. Integration must accept them explicitly or supply a reviewed adapter.

## Explicit interface

prepare_retention_plan(state, *, roles, archive_ids, limits) returns frozen
RetentionPlan(active_json, manifest_json, archives). Inputs are exact JSON
builtins. All source IDs must have a role supplied in a plain dict: pending,
authority, cold_history or unknown. Only explicit trusted non-authority-bearing cold_history IDs in archive_ids can
move. A literal pending status vetoes movement even if misclassified as history.
No status or timestamp automatically establishes history eligibility. Authority
and unknown IDs remain active. No subset, absent ID or repeated ID is accepted.
A nonobject record cannot be selected. Nonselected JSON values are preserved,
not blessed as semantically valid approval records.

SC-J05 must define and validate records and supply trustworthy classifications.
Approved records can be authority-bearing long after decision. Rejected records
can also be needed for audit or subsequent decision logic. Caller classification
is not proof of authorization. A malicious/wrong cold_history label other than the
pending veto is not independently detected. Do not wire the helper until this
classification boundary is settled.

Every RetentionLimits field is required: source/active/archive value and byte
caps, manifest byte cap, depth. Active values cannot exceed 10,000 and depth
cannot exceed 64. Lower active caps can reserve headroom, but no headroom amount
is chosen here. Value counts match SC-J04 JSON-expanded counting, not byte size.
Canonical encoding uses sorted keys, ASCII escapes and compact separators;
byte limits cover these bytes, not gate.py's indented encoding. A caller must
independently verify real write/storage budgets and projected next operations.

Archive shards are selected in sorted-ID order and greedily bounded by supplied
caps. Full records are kept; oversized individual records fail rather than being
split/truncated. Artifacts are exact bytes plus SHA-256 fingerprints. Manifest
contains all source IDs/roles, canonical source fingerprint/count/byte length,
active descriptor and archive descriptors with exact membership and counts.
No archive pathname, store identifier, TTL or lookup binding is invented.

replay_retention_plan(*, manifest_json, active_json, retrieved, limits) requires
a Mapping from exact archive fingerprint to bytes obtained by the integrator.
Missing, extra, repeated, overlapping, corrupt, truncated or noncanonical
artifacts fail closed. Duplicate keys and nonfinite JSON fail. Active/manifest
fingerprints, exact membership, counts, deterministic partition and source
fingerprint are checked by re-deriving the complete plan. Aggregate source value
and byte caps are checked while merging. Returns the whole detached JSON state
only after verification, never a partial return or an approval decision.
Malformed values raise InvalidRetentionPlan for supported validation errors.
Storage retrieval failures, MemoryError and IO errors are not normalized; caller
must fail closed. Byte caps bound parse input but are not streaming-parse memory
or CPU guarantees. Integer conversion limits are interpreter-dependent. No
concurrent caller-mutation isolation or hostile custom Mapping guarantee.

## NO-LOSS policy proposal for peer/owner decision

Retain original active state as authoritative until every proposed full-record
archive and manifest is durably stored, retrieved independently and replayed to
the exact canonical source. Keep pending requests, authority records and unknown
records active. Archive means relocation with supported retrieval, never deletion
of facts. Preserve originals/recovery generation through commit verification;
choose its duration explicitly. No silent record purge or TTL expiry.

Proposed integrator ordering, NOT implemented:

1. Hold a shared cross-process lock. Validate trusted schema/classification and
   capture source generation/fingerprint. Validate requested retention authority.
2. Prepare a bounded plan with reviewed eligibility and capacity/headroom inputs.
3. Write immutable full-record shards. Establish durability using the selected
   storage protocol, not successful in-memory encoding or a hash alone.
4. Durably store a trusted manifest, independently retrieve every artifact and
   replay all source data. Any missing artifact/read/write error stops the commit.
5. Recheck authoritative source generation under the same lock. On change abort
   and replan; never overwrite newer requests/decisions. Stage active/index state
   and commit atomically with a defined durable recovery protocol.
6. Verify readback and gate decision lookup across active AND archived sources.
   Keep old authority/recovery until this succeeds. Partial/crashed commits use
   the documented recovery source, never a guessed newest file.

Hashes detect accidental corruption relative to a trusted manifest; they do not
prove authorship, human consent or authenticity. An attacker able to replace the
manifest and artifacts can fabricate a consistent history. SHA-256 fingerprints
also are not a storage receipt or supported retrieval route.

## Open decisions, no inferred defaults

- SC-J05 schema, roles, decision transitions and classification provenance.
- Which history IDs may move, retention age/criteria and later revocation rules.
- Which decisions are still needed by decision(approval_id), and the active plus
  archive lookup/index API. Today gate.decision reads only the active file.
- Active headroom for future requests and decisions, maximum payload/actor field
  growth, record sizes, source/archive/manifest caps and behavior when exceeded.
- Archive storage identity, access/authenticity controls, independent retrieval,
  backup, corruption repair, durability and cost. No new service proposed.
- Atomic commit and cross-process locking, generation comparison, recovery and
  old-generation retention. Existing gate write_text does not provide them.
- Eventual removal from active state and backup purge authority. No live deletion
  or retention-policy action is authorized by this helper's existence.

This is bounded finite-history prep, not an unlimited-history claim. Source and
manifest caps can themselves be reached. If protected active data alone exceeds
its budget, planning fails and operator/peer policy work is required; it does not
silently remove pending requests or authority to make room.

## Authored-not-run evidence and peer-owned next steps

Authored canaries cover complete valid replay, detached snapshots, accumulating
history above the SC-J04 ceiling, deterministic shards, protected/unknown roles,
explicit pending veto, capacity/serialization failure, corrupt/missing retrieval,
manifest tampering, duplicate keys and nonfinite data, invalid policy limits.
Crash-cut tests are a pure protocol MODEL that asserts the original remains
untouched before commit. They are not filesystem/process-crash evidence.

Peer must run the authored tests, validate SC-J05 adapter decisions, implement
and execute real disk-full, interrupted-write, fsync/rename, missing-archive,
stale-generation, cross-process, crash-after-commit and rollback/restart canaries,
and independently verify full gate wiring and decision replay. No tests,
pytest, services, PostgreSQL or Alembic were run by this prep unit. No main write,
push, existing-path edit, migration, secret/env read or live archive occurred.
