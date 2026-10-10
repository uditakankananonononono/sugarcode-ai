# UNIT B - Compatibility contract: optional expected-record fingerprint + decision transitions

Status: PROPOSED CONTRACT ONLY (PREP-NORUN). No implementation exists or is
claimed. Base 6e1a42145e529d50751ec3b5cedc6d6ff3105f60. Landing any of this
requires owner-approved implementation and independent audit execution.
Companion analysis: docs/prep/unit-b-decision-envelope-report.md.

## 1. Canonical record fingerprint (proposed)

Definition (reference implementation lives inside the authored test file,
not in product code):

    fingerprint(record) = sha256(
        json.dumps(snapshot_json(record),
                   sort_keys=True, separators=(",", ":"),
                   ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()

Properties and raw-vs-semantic distinctions:

- SEMANTIC, not raw: the input is the decoded record passed through the J04
  snapshot rules (exact builtins, tuples become arrays, finite numbers,
  string keys). Two different raw byte strings - different key order,
  whitespace, indentation, or Unicode-escaped equivalent keys - that decode
  to the same semantic record yield the SAME fingerprint. Raw-byte hashing
  is explicitly rejected: the gate never retains raw bytes per record, and
  J04 re-serializes on every save, so raw bytes are not stable identity.
- int vs float ARE distinct semantics: canonical dumps render 1 as `1` and
  1.0 as `1.0`, so a numeric-type change in any field changes the
  fingerprint. This is intentional: it matches the exact-builtin typing the
  schema enforces.
- The fingerprint covers the WHOLE envelope (identity, payload, status,
  timestamps, decided_by). It does not authenticate the author of any
  field; it only proves "the record I decide on is byte-for-byte the
  semantic record I reviewed".
- Records that snapshot_json refuses (cycles, non-builtins, nonfinite
  numbers, depth > 64, > 10,000 expanded values) have no fingerprint;
  such records already cannot be saved by the gate.

## 2. Optional expect_fingerprint on decide (proposed)

Proposed signature: decide(approval_id, decision, *, decided_by="human",
expect_fingerprint=None).

- expect_fingerprint=None (DEFAULT) reproduces current behavior exactly.
  This is REQUIRED for compatibility: generic legacy status-only records,
  the actual auto_approve gate flow, and every existing caller
  (engine-free scripts, existing tests) call decide without a fingerprint.
- When a fingerprint is supplied: compute it over the stored record BEFORE
  mutation, inside the gate lock; mismatch raises PermissionError and
  leaves the file unchanged. Unknown approval_id still raises KeyError.
- The review-side helper (e.g. gate.record_fingerprint(approval_id) or a
  free function over the detached record from gate.record()) is part of
  the same proposal; either shape satisfies the contract as long as the
  reviewer fingerprints exactly the semantic record they read.
- Non-goals: no replay protection across gate files, no signer identity,
  no protection against a noncooperating writer who replaces the whole
  file (advisory locks and fingerprints both fail there; stated in
  approval-consumption-locks.md).

## 3. Decision transitions (proposed, two options)

Option A (DEFAULT, compatible): current transition behavior - any
pending/approved/rejected record can be re-decided to approved or
rejected. Preserves the documented revoke-unused / restore-unused
mechanism (docs/approval-consumption-locks.md) and existing tests.

Option B (OPT-IN strict, e.g. ManualApprovalGate(strict_transitions=True)):
- Allowed: pending->approved, pending->rejected.
- Refused (PermissionError, file unchanged): approved->approved,
  approved->rejected, rejected->approved, rejected->rejected.
- Legacy status-only records: same table applied to their status value;
  they are NOT exempt from strict mode (their status is always known).
- Auto-gate exception: records created approved-with-unrecorded-decision
  under auto_approve keep their existing shape; the first real decide() on
  such a record is treated as pending->decision for transition purposes
  ONLY if the owner approves that reading - flagged as an open semantic,
  because today auto-gate records are flippable like any other.
- Option B removes the documented revoke-unused mechanism. That is a
  behavior deletion, not a bug fix; it needs explicit owner approval and a
  replacement revocation path (e.g. a distinct recorded "revoked" status),
  which this contract does not define.

## 4. Decision-event history (proposed, pairs with Option B)

- New optional record key "decision_history": a list of entries
  {"status", "decided_at", "decided_by", "envelope_fingerprint"}, one per
  superseded decision, appended BEFORE each overwrite. validate_record's
  allowed-key set must be extended; entry schema mirrors the decision
  fields; decided_by stays unauthenticated (null allowed, J04 compat).
- Budget accounting (required by acceptance): every history entry lives in
  the same state object, so each entry's expanded values count against the
  J04 snapshot_json 10,000-value whole-state budget and the serialized
  bytes against APPROVAL_FILE_BYTES (4 MiB). A state at the ceiling
  refuses the next decide that would append - fail-closed, state
  unchanged, per the existing _save boundary. Long-term relief is the
  SC-H01 retention partition (docs/sc-h01-approval-retention-contract.md);
  this contract does not implement retention.
- Option A (flips without strict transitions) MAY also append history;
  history and strictness are independent knobs, but history without
  strictness still preserves the overwritten envelopes that strictness
  would have refused.

## 5. Timestamp semantics (proposed additions to validate_record)

- Decided records: require decided_at >= requested_at. Pending records:
  decided_at must stay None (already enforced).
- Reject negative requested_at/decided_at, aligning the gate with the
  consumption record domain (consumed_at >= 0 in approval_consumption).
- With history: entry decided_at values must be nondecreasing and each
  <= the live decided_at.
- No wall-clock or future comparison: the gate stays clock-independent;
  "future" relative to a real clock is not validated.
- Legacy status-only records and the auto-gate unrecorded-decision shape
  are exempt (they lack the fields these checks read).

## 6. Unresolved semantics (need owner/integrator decision)

1. Option A vs Option B as the shipped default; Option B's deletion of
   flip-to-revoke needs a revocation replacement.
2. Auto-gate records under Option B: is the first real decide a fresh
   pending->decision, or refused like other re-decides?
3. History retention: unbounded growth until the J04/4 MiB ceiling refuses
   saves, or block landing until SC-H01 retention ships?
4. Fingerprint helper surface: method on the gate vs free function over
   detached records.
5. Whether expect_fingerprint failures and transition refusals reuse
   PermissionError (consistent with engine mapping) or a new typed error.
