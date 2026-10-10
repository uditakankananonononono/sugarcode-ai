# SC-J05 approval request/status schema: prep contract

Status: PREP ONLY. Helper and tests authored, tests NOT run, nothing wired.
The helper existing is not a completed repair.

## Interface
`sugarcode.self_improve.approval_schema` (pure, no I/O, no gate/engine import):
- `validate_record(record, *, allow_unrecorded_decision=False)`
- `validate_payload(action_type, payload)`
- `check_binding(record, ActivationExpectation | RollbackExpectation) -> status`
- `require_approved(record, expectation)`; PermissionError if well-formed but not approved.
- `ApprovalSchemaError(code)`; messages carry only a reason code.

## Schema frozen here (from gate.request and engine.propose/request_rollback at ba0eb275)
Record keys: module_id (exact int), module_slug, action_type (non-empty str), summary (str),
payload (dict), status in pending/approved/rejected, requested_at, decided_at (finite number or
null); optional decided_by (non-empty str or null; null accepted because SC-J04 main 35998c7 lets decide(decided_by=None) through). Unknown keys refused.
Activation payload keys exactly: candidate_key, name, kind, code_sha256 (64 lowercase hex),
gap_signature. Rollback payload keys exactly: feature.

## Pending integration (owned by the peer/integrating side, not done)
1. gate.decision()/decide(): call `validate_record` on the stored record before returning status.
2. engine.activate(): needs the gate to expose the full record (no read API exists; `decision()`
   returns only status). Interface needed, e.g. `gate.record(approval_id)`. Not invented here.
3. engine.rollback(): same read API, plus SC-A01 expected-approval binding (request_rollback
   does not store its approval_id in the registry today). `RollbackExpectation` is the pure half.
4. SC-J04 (peer-owned, read at main 35998c7): writer snapshots exact builtins, allow_nan=False,
   InvalidApprovalState on bad writes; no semantic schema. Not duplicated. Reconciled: decided_by null
   accepted; JSON-roundtrip of records still binds. Note write_text is still nonatomic (SC-F01) and
   history growth may refuse saves; unaddressed here.

## Open decisions
- auto_approve gates write approved with decided_at null and no decided_by. Default refuses;
  flag `allow_unrecorded_decision=True` accepts. Decide which production/legacy policy applies.
- A decided record with decided_by null is accepted (attribution-free); tighten if policy wants a named decider.
- Legacy approvals.json with other shapes will be refused; no migration policy defined.
- `summary` content is not bound to the operation (free text).
- Does NOT authenticate a human or file editor; matching metadata is not authority.
