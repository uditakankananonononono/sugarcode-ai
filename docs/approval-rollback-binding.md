# Rollback approval target binding (SC-A01 PREP ONLY)

Base: published 35998c7efc977a4682abb5e2e410d62ee4a4e3fd (main after the
verified approval JSON write-boundary merge; ba0eb275 is an ancestor).
Status: PREP ONLY contribution - pure helper, authored tests and this
contract. No existing file is edited, no test was executed by the builder,
no wiring exists. A helper existing is NOT the completed repair;
integration, test execution and the independent verdict belong to the
integration owner.

## Vulnerability

`SelfImprovementEngine.rollback()` checks only
`gate.decision(approval_id) == APPROVED`. Unlike `activate()`, which
compares the approval id recorded on the registry proposal, rollback never
verifies the approval was requested for this feature, module, or action.
Consequences on the current base:

- an approved ACTIVATION approval id rolls back any active feature;
- an approved rollback requested for feature A rolls back feature B;
- an approved rollback requested on module X rolls back a feature on
  module Y sharing the same gate file.

`TestEngineWiringCanaries` in tests/self_improve/test_approval_rollback_binding.py
encodes these as failing canaries on the pre-wiring base.

## What this prep adds

`src/sugarcode/self_improve/approval_binding.py`:

- `rollback_target(record)` - shape-checks a stored gate record and
  extracts (module_id, module_slug, action_type, payload.feature).
  Exact-builtin typing: bool is rejected as module_id, non-strings as
  slug/action/feature. Unknown extra keys tolerated. Decision status is
  deliberately NOT inspected - status stays the gate's decision check and
  the SC-J05 schema's concern.
- `validate_rollback_binding(record, *, module_id, module_slug,
  feature_name, current_active_version=None)` - raises
  `ApprovalBindingMismatch` for a well-formed approval requested for a
  different action/module/feature (the replay cases), and
  `InvalidApprovalRecord` for records lacking the required shape.
- Optional version pinning: a payload `active_version_at_request` (int or
  null) must equal the caller-supplied current active version, so an
  approval cannot roll back a version newer than the state the human saw.
  Nothing writes this key today; unpinned records return
  `BindingReport.version_bound=False`, a documented weaker binding.
- `ApprovalRecordSource` Protocol + `validate_rollback_request(...)` -
  fetch-then-validate convenience against a full-record read API.

## Dependencies and open decisions

1. SC-J05 (peer-owned, pending): the request/status schema and read API.
   `ApprovalRecordSource.record(approval_id) -> Mapping` is this unit's
   PROPOSED minimal interface (full record, KeyError for unknown ids, J05
   error type for schema failures). It is not the frozen J05 contract; the
   validator depends only on the mapping it is handed, so any J05 read
   shape returning the record mapping works unchanged.
2. Payload contract: `engine.request_rollback()` already writes
   `payload={"feature": name}`; J05 must freeze key `feature` for binding
   to remain enforceable. Activation payloads are intentionally not bound
   to rollback by this helper.
3. Integration wiring (NOT done here): `engine.rollback()` should call
   `validate_rollback_request(<J05 read API>, approval_id, module_id=...,
   module_slug=..., feature_name=feature_name, current_active_version=
   registry.features()[name]["active_version"])` after the existing
   decision check and map ApprovalBindingError to PermissionError.
   `engine.request_rollback()` should additionally record
   `payload["active_version_at_request"]` so new approvals are
   version-pinned; until then version_bound=False applies.
4. Done criteria from the inventory map to TestEngineWiringCanaries:
   approval for a different feature/module/action cannot roll back the
   target; a correct rollback request can; missing/inactive features raise
   KeyError; canaries exercise real state transitions (real engine,
   registry and gate file in tmp dirs).

## Limits

Metadata matching only - no actor authentication, no cryptographic
authority, no proof a human decided anything. A local actor who can write
the gate file can fabricate a well-formed approved record. Decision-status
enforcement remains the existing gate check; status/request schema beyond
the fields binding reads remains SC-J05. No claim about atomicity,
cross-process locking, or the accumulating-history ceiling documented in
docs/approval-json-write.md.

## Builder evidence statement

No tests were run: prep constraints forbid executing pytest. Both new
Python files pass `python3 -m py_compile` only. Expected behavior when the
integration owner runs the suite: TestEngineBindingValidator and
TestRecordSourcePath pass standalone on this branch;
TestEngineWiringCanaries mismatch cases FAIL until the wiring in
"Dependencies and open decisions" item 3 lands - that failure on the
unwired base is the intended detection canary, and the positive cases
(correct request rolls back, pending refused, missing/inactive KeyError)
must pass before and after.
