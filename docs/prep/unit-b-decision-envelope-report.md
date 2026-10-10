# UNIT B - Decision envelope/time semantics + decision-history preservation (report)

Status: PREP-NORUN analysis. Authored from reading the public repo at base
6e1a42145e529d50751ec3b5cedc6d6ff3105f60 (verified resolving; source
https://github.com/uditakankananonononono/sugarcode-ai). No code was executed
for this report; every "current" claim below is a code-reading claim, and each
has a corresponding authored test in
tests/self_improve/test_decision_envelope_semantics.py that our side executes
in audit. Nothing here is a repair. Proposed semantics require later
owner-approved implementation; the compatibility contract lives in
docs/prep/unit-b-decision-envelope-compat-contract.md.

## 1. Current-vs-proposed table

| Semantic | NOW (base 6e1a421, code reading) | Proposed (contract doc) |
|---|---|---|
| Decision value domain | Enforced: decide() accepts only "approved"/"rejected" (ValueError otherwise) | Unchanged |
| approved<->rejected flip | Enforced as ALLOWED: decide() has no transition guard; any record with a valid status string can be re-decided. This is documented policy in docs/approval-consumption-locks.md ("a later REJECTED decision can revoke unused approved records; a later APPROVED decision can restore UNUSED request permission") and exercised by existing tests | Option A (default, compatible): flips remain allowed. Option B (opt-in strict): pending->approved/rejected terminal; decided records refuse re-decide |
| Envelope rewrite on re-decide | decide() unconditionally overwrites status, decided_at, decided_by on the SAME envelope; previous decision values are lost | History is a knob INDEPENDENT of strictness (contract section 4): with history on, every re-decide appends the prior decision to decision_history before overwrite (Option A or any re-decide-permitting mode); without it the overwrite stays lossy. Under strict Option B re-decides are refused, so no superseded decision exists to append |
| Decision-event history | Absent on MANAGED FULL envelopes: the record schema (approval_schema.RECORD_REQUIRED/OPTIONAL) has no history field and validate_record REFUSES unexpected fields, so a schema-validated record cannot carry history. Legacy status-only records are NOT covered by this: decide() skips validate_record when "action_type" is absent, so a decision_history key on such a record survives direct save/decide unexamined | Adds decision_history to the allowed-key set as a knob independent of strict transitions; every entry counts against the J04 whole-state snapshot budget (10,000 expanded values) and the 4 MiB APPROVAL_FILE_BYTES cap |
| Expected-envelope fingerprint at decide | Absent: ManualApprovalGate.decide signature is (approval_id, decision, *, decided_by); coordinated_record yields the LOCK identity (resolved path string), not a record fingerprint; engine checks only that identity is a nonempty string | Optional expect_fingerprint parameter: sha256 over the canonical JSON of snapshot_json(record); None preserves current behavior (required for legacy and auto-gate flows) |
| requested_at <= decided_at ordering | Not enforced: validate_record checks only that both are finite int/float (or decided_at None); a stored record with requested_at greater than decided_at passes validation and decide() succeeds on it | Proposed check in validate_record (decided records only); legacy and auto-gate shapes exempt per their existing exceptions |
| Negative timestamps | Accepted: _is_number admits negative int/float for requested_at/decided_at. NOTE: approval_consumption.validate_consumptions requires consumed_at >= 0, so the gate and consumption time domains already differ | Proposed: reject negative requested_at/decided_at in validate_record; aligns gate with consumption domain |
| Future timestamps | Accepted: no upper bound or clock comparison anywhere | Proposed: no wall-clock comparison (gate must stay clock-independent for testability and file portability); instead require monotonicity per record (decided_at >= requested_at and, with history, nondecreasing across entries) |
| Decider identity | NOT authenticated: decided_by is a free-form string; null accepted and stored as JSON null (documented J04 compatibility, tested by test_approval_schema.py::test_decided_by_null_accepted_per_j04_contract). decide() default "human" is a label, not verification | Unchanged: the contract explicitly keeps decided_by unauthenticated metadata; no identity claim is added |
| Auto-gate exception | Preserved now: auto_approve=True writes status approved with decided_at None and no decided_by; validate_record(allow_unrecorded_decision=True) admits exactly that shape; engine passes the flag only for exact-type ManualApprovalGate with _auto True | Preserved unchanged; fingerprint/history proposals exempt the auto-gate shape or treat first real decide() as the history start |
| Legacy status-only records | Preserved now: decide() and record() validate only the status field when "action_type" is absent (schema validation is skipped for such records); they can be decided and flipped | Preserved unchanged; legacy records are exempt from fingerprint requirement (fingerprint optional everywhere) and from schema-level timestamp checks |

## 2. Stale-review and edited-payload scenarios that REMAIN despite cooperating locks

Locks (state_lock.py) are advisory and path-keyed; they order cooperating
processes only. Reading the code:

1. Stale review among cooperating actors: gate.record() returns a DETACHED
   snapshot. A reviewer reads at time T; any cooperating decide() at T+n
   changes status/decided_at/decided_by; the reviewer's later decide() then
   overwrites that decision based on a stale view. Locks serialize the
   writes but do not tell the second decider the envelope changed since the
   review. An expected-envelope fingerprint is ONE way to close this;
   alternatives exist (compare-and-swap on the full detached record, a
   monotonic revision counter checked at decide, or holding the gate
   lock continuously across review and decide). The contract proposes
   the fingerprint; which mechanism, if any, ships is OPEN.
2. Edited payload before decide: no cooperating API mutates payload after
   request(), but a NONCOOPERATING editor (or any process that ignores the
   sidecar lock) can rewrite approvals.json between review and decide.
   decide() re-validates the edited record and approves it as-is; nothing
   compares against what was reviewed. The only existing backstop is
   downstream: engine activate/rollback re-binds payload identity via
   approval_schema.require_approved at commit time. A payload edited to
   still-match the expectation (e.g. summary text, or a rollback payload
   whose feature is unchanged but whose requested_at moved) is approved
   undetected.
3. Flip after consumption: engine commit consumes (gate_identity,
   approval_id) into the registry atomically with the effect. A later
   decide() flip (approved->rejected) succeeds and rewrites the envelope,
   but the registry effect and consumption record remain; re-commit with
   the same id refuses as consumed. Result: gate says rejected, registry
   says committed, and with no decision-event history there is no record
   of the approved state that authorized the commit. Documented in
   approval-consumption-locks.md as "commit winning first remains
   effective; no retroactive undo" - the gap is the ABSENCE OF HISTORY,
   not the barrier itself.
4. Rollback pin vs new active version: COVERED at this base.
   request_rollback pins payload["active_version_at_request"];
   engine.rollback re-checks the pin against the registry's current active
   version inside the registry lock, and approval_binding.validate_rollback_binding
   re-checks the binding. Existing tests: test_rollback_version_pin.py (7
   tests) plus test_approval_consumption_integration.py. This unit authors
   no duplicate; see section 4.

## 3. Spec-vs-code contradictions and overlaps flagged BEFORE authoring

1. One-shot transitions vs documented revoke: treating "decide freely
   flips" purely as a defect contradicts approved policy at this base -
   docs/approval-consumption-locks.md documents flip-to-revoke-unused and
   flip-to-restore-unused, and
   test_approval_consumption_integration.py::test_revoke_before_lock_winner_refuses_then_reapprove_unused
   depends on it. Removing flips without an owner decision would delete a
   tested revocation mechanism. The contract therefore defaults to flips
   allowed (Option A) and makes strict transitions opt-in (Option B).
2. Time-domain inconsistency (pre-existing): gate schema accepts negative
   requested_at/decided_at; consumption records require consumed_at >= 0.
   The report flags it; the proposal aligns the gate to the stricter rule.
3. record() asymmetry: gate.record() never calls validate_record (status
   shape only), so a malformed full record can be read and snapshot
   returned; schema enforcement happens at request/decide (when
   action_type present) and at engine binding. Not changed by this unit;
   recorded here because "record/coordinated_record" were in scope.
4. Duplication avoided: "rollback pin vs new active version" and
   approve/reject unused-vs-consumed barrier semantics are already covered
   by test_rollback_version_pin.py and test_approval_consumption_integration.py
   at this base. This unit adds only the envelope/history-focused cases
   those files do not assert (post-commit flip divergence without history;
   unused flip guard).

## 4. Acceptance-caveat compliance

- No claim that timestamp ordering exists: section 1 states ordering is
  NOT enforced; test_requested_at_after_decided_at_accepted proves the gap.
- No claim that decider identity is authenticated: decided_by stays
  unauthenticated metadata in both current and proposed columns.
- Real gate tests reveal the mutable approved envelope and absent history:
  TestCurrentDecideEnvelope asserts flips, overwrite, and the exact
  post-decide key set (no history field survives).
- Append-history counts against the J04 ceiling: the proposed history is
  part of the same state object snapshotted by gate._save through
  snapshot_json (10,000 expanded values) and capped at APPROVAL_FILE_BYTES
  (4 MiB); test_appended_history_counts_against_j04_budget exercises the
  budget directly. Interaction with SC-H01
  (docs/sc-h01-approval-retention-contract.md): history growth is the
  kind of pressure that contract partitions, but whether history waits
  for SC-H01, lands unbounded until the ceiling refuses saves, or is
  bounded some other way is an OPEN owner/integrator choice (contract
  section 6). No relief mechanism is asserted here.
- Generic legacy and actual auto-gate exceptions preserved: sections 1 and
  the contract carry both as explicit exemptions; guard tests authored.
