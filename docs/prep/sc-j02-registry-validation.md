# SC-J02 registry validation preparation

Status: PREP ONLY. Tests authored, not run. No repair completion, integration,
activation/dispatch protection, or independent verdict is claimed.

Base: ba0eb275f182e77a4f24530b668e3e17f2528df5.
Source: src/sugarcode/self_improve/registry.py, plans.py and existing registry tests.
The production registry still uses bare json.loads and direct write_text.

## Explicit proposed interface

- decode_registry_json(raw: exact str | bytes, *, expected_module: str) -> dict
- validate_registry_state(state, *, expected_module: str) -> same input dict
- Both raise RegistryValidationError (ValueError subclass) on refusal.
- No imports of gate, registry, persistence helpers or approval-reader helpers.
- No file reads/writes, conversions, repairs, defaults or schema migration.
- Bytes decode strictly as UTF-8, with no BOM or UTF-16 auto-detection.
- Duplicate object keys anywhere, NaN/Infinity, float overflow, nonobject roots,
  malformed JSON and trailing content refuse. Decoded state and unknown fields
  must contain only exact builtin JSON types and finite floats; cycles refuse.
- Validate full registry, not just the feature selected by an operation.
- Returned state remains mutable. Revalidate after modifications before encoding
  and before effects. This is not a capability, snapshot lock, or approval token.

## Proposed minimal compatible schema (peer decision pending)

Required top-level fields: module string matching caller's expected_module,
features object and proposals object. Unknown finite JSON fields are preserved
at every level to avoid undocumented data loss; they do not grant authority.

Module, feature/proposal IDs and proposal names are nonempty strings made from
alphanumeric characters, underscores and hyphens, with at least one alphanumeric
character. Unicode alphanumerics remain accepted to match existing slug logic.
No slash, backslash, dot, traversal or empty identifier. This is a proposed new
ID boundary, not proof that all historical direct callers used safe names.

Each feature requires versions array and active_version null or exact positive
integer referring to a version. Versions must be ordered contiguous 1..N, since
activate uses len(versions)+1. Bool/float IDs, duplicates, gaps, reordering and
dangling active_version refuse. An empty history with null active version is valid.
A rollback may reactivate an older version that has past rollback metadata.

Each version requires version, file, sha256, kind, gap_signature, approval_id,
activated_at. file/kind/approval_id are nonempty strings; gap_signature may be
empty. SHA-256 is exactly 64 lowercase hex characters. Timestamps are nonnegative
exact int/float, never bool, finite. dispatch_count is optional for compatibility
with the existing .get(..., 0) read, and when present is an exact nonnegative int.
last_dispatched_at is optional. rolled_back_at and rollback_approval_id are paired;
rollback approval IDs are nonempty strings. No enum for kind: direct registry API
accepts arbitrary nonempty kinds, unlike FeaturePlan's six-kind planner API.

Each proposal requires name, kind, gap_signature, code_sha256, test_sha256,
code_file, test_file, approval_id, status, created_at. Hash/string/time constraints
match version fields. Status is exactly proposed or activated (only statuses
written by current registry). Proposal approval_id may be null even when activated:
direct FeatureRegistry.activate does not set the proposal approval ID. Do not
invent a cross-record binding to versions: current version entries lack proposal
IDs and direct activation accepts a separate approval ID.

## Decisions needed before integration

1. Adopt or change the proposed ID rules, contiguous version ordering, timestamps,
   rollback-pair invariant and status enum. Reject historical incompatible states
   or define an explicit reviewed migration; never silently normalize them.
2. Keep extension fields as finite JSON or adopt a closed-key schema. Current prep
   preserves extensions; an unknown field does not change validation semantics.
3. Wiring owner decides translation to existing RegistryError and read/preflight
   placement. Validate before activation, dispatch and mutation effects, and again
   before serialization. Simply replacing _load is insufficient: save_proposal
   writes candidate files before _load (SC-R01), while other operations copy/run
   files before final state writes. Concurrency/TOCTOU are not solved here.

## Boundaries and remaining verification

No SC-J04 dependency: this helper does not implement gate serialization, approval
payload schemas, approval reads, human authentication, signatures or authorization.
It only validates structure and local references. File string validation is not
path containment or existence/hash verification. Keep _contained and digest
checks, and separately decide path consistency in SC-R01. No claim of matching
proposal approval IDs to gate decisions. No new services, PG or migrations.

SC-F02 owns file/line budgets. This decoder has no predecode byte, depth or CPU
budget and makes no universal resource containment claim. Recursion errors from
JSON parsing refuse, but process memory exhaustion is not contained. SC-F01 owns
single-file atomic persistence. Cross-file transactions and exactly-once effects
are not implemented.

The fixture module covers empty, proposed, activated, dispatched and rolled-back
legacy shapes. The authored lifecycle test reads output from the real existing
registry writer and exercises two activations, dispatch and both rollbacks.
Adversarial tests cover ambiguity, nonfinite values, invalid nested shapes/IDs,
active references, missing fields, custom Python hooks, cycles and unchanged read
bytes. They are not results. The peer must run these and production canaries after
wiring and obtain its independent verdict. No tests or production APIs were run
as part of this preparation.
